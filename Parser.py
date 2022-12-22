import logging

import pycparser as pyc

from .CObj import CObj
from .CFunc import CFunc

class Parser:
    def __init__(self, logger : str = "") -> None:
        """
        # Description:
            Constructor of Parser.
        
        # Parameters:
            logger:
                The name of the logger.
                The logger uses logging in the python standard.
        """
        if(logger):
            self.logger = logging.getLogger(logger)
        else:
            self.logger = None


    def parse_code(self, code : str) -> list:
        """
        # Description:
            Parse code and return a list of CObj.

        # Parameters:
            code:
                A string containing the C source code.

        # Return:
            A list of CFunc.
        """
        parser = pyc.c_parser.CParser()
        ast = parser.parse(code)
        return self._parse_ast(ast)


    def parse_file(self, path : str, 
        use_cpp : bool = False, cpp_path : str = 'gcc', 
        cpp_args : list = [], parser = None
        ) -> list:
        """
        # Description:
            Parse file and return a list of CObj.

        # Parameters:
            path:
                Path of the file you want to parse.
            
            use_cpp:
                Set to True if you want to execute the C pre-processor
                on the file prior to parsing it.

            cpp_path:
                If use_cpp is True, this is the path to 'cpp' on your
                system. If no path is provided, it attempts to just
                execute 'cpp', so it must be in your PATH.

            cpp_args:
                If use_cpp is True, set this to the command line arguments
                strings to cpp. Be careful with quotes - it's best to pass a
                raw string (r'') here. For example:
                r'-I../utils/fake_libc_include'
                If several arguments are required, pass a list of strings.

            parser:
                Optional parser object to be used instead of the default 
                CParser.

        # Return:
            A list of CObj.
        """
        return self._parse_ast(
            pyc.parse_file(path, use_cpp, cpp_path, 
                cpp_args, parser
            )
        )


    def _parse_ast(self, ast : pyc.c_ast.Node) -> list:
        func_list = []

        for node in ast.ext:
            if isinstance(node, pyc.c_ast.FuncDef):
                # Is FuncDef.
                self._add_to_func_list(node.decl, func_list)

            elif(isinstance(node, pyc.c_ast.Decl) 
                and isinstance(node.type, pyc.c_ast.FuncDecl)
                ):
                # Is FuncDecl.
                self._add_to_func_list(node, func_list)
                
        return func_list


    def _add_to_func_list(self, 
        func_node : pyc.c_ast.Decl, target_list : list
        ) -> list:
        # Get function name.    
        func_name = func_node.name

        # Check if function has been added to the list.
        for func in target_list:
            if func_name == func.name:
                return target_list

        # Add function to list.
        func = None
        try:
            func = self._ast_to_c_obj(func_node)
        except self.ParserNotImplementedError as e:
            if(self.logger):
                self.logger.warning("Parse function error: " + func_name + \
                    " error: "+ str(e)
                )

        if(func is not None):
            if(isinstance(func, CFunc)):
                if(self.logger):
                    self.logger.info("Parse function: " + func_name)
                target_list.append(func)
        else:
            return target_list

        return target_list

    
    def _ast_to_c_obj(self, node : pyc.c_ast.Decl) -> CObj:
        """
        # Description:
            Convert function, c object, function param to CObj.
            Only function declaration, c object declaration and function param
            are supported.

        # Return:
            c function in CFunc or c object in CObj.
        """
        # pyc.c_ast.Decl has the following properties:
        ##  name:       the variable being declared
        ##  quals:      list of qualifiers (const, volatile, restrict)
        ##  align:      byte alignment.
        ##  storage:    list of storage specifiers (extern, register, etc.)
        ##  funcspec:   list function specifiers (i.e. inline and _Noreturn_)
        ##  type:       declaration type.
        ##  init:       initialization value, or None
        ##  bitsize:    bit field size, or None
        c_obj_name = ""
        c_obj_quals = []
        c_obj_align = []
        c_obj_storage = []
        c_obj_funcspec = []
        c_obj_type = ""
        c_obj_pointer_layers = 0
        c_obj_array_layers = 0
        c_obj_params = []

        is_function = False

        # process Decl
        if(isinstance(node, pyc.c_ast.Decl)):
            # Get name.
            c_obj_name = node.name
            
            # Get qualifiers.
            c_obj_quals = node.quals

            # TODO: align
            if(len(node.align) > 0):
                raise NotImplemented("Align is not supported temporarily.")
            
            # Get storage specifiers.
            c_obj_storage = node.storage

            # Get funcspecs.
            c_obj_funcspec = node.funcspec

            # Check type.
            if(isinstance(node.type, pyc.c_ast.ArrayDecl)):
                c_obj_type, c_obj_array_layers, c_obj_pointer_layers = \
                    self._get_nesting_type(node.type)

            elif(isinstance(node.type, pyc.c_ast.Decl)):
                # I don't think Decl should appear, but it needs to be verified.
                raise Exception("The Decl should no longer appear in the Decl.")

            elif(isinstance(node.type, pyc.c_ast.Enum)):
                # Enum, such as:
                # Declaration:
                #   enum enum_type { a, b, c };
                # Object:
                #   enum_type obj; // Type of obj is enum.
                # Type name:
                #   name    -> enum_type
                c_obj_type = "enum " + node.type.name

            elif(isinstance(node.type, pyc.c_ast.FuncDecl)):
                is_function = True
                # Get params.
                for param in node.type.args:
                    c_obj_params.append(self._ast_to_c_obj(param))
                # Get type.
                c_obj_type, c_obj_array_layers, c_obj_pointer_layers = \
                    self._get_nesting_type(node.type.type)

            elif(isinstance(node.type, pyc.c_ast.PtrDecl)):
                # Pointer declaration, such as:
                #   int *a;
                c_obj_type, c_obj_array_layers, c_obj_pointer_layers = \
                    self._get_nesting_type(node.type)

            elif(isinstance(node.type, pyc.c_ast.TypeDecl)):
                # TypeDecl, such as:
                #   int a;
                c_obj_type, c_obj_array_layers, c_obj_pointer_layers = \
                    self._get_nesting_type(node.type)

            elif(isinstance(node.type, pyc.c_ast.Typename)):
                # Typename, such as:
                #   void func(int);
                # Then `int`` in the params is Typename.
                c_obj_type, c_obj_array_layers, c_obj_pointer_layers = \
                    self._get_nesting_type(node.type.type)
                
                raise Exception("TODO.")

            else:
                # such as: ArrayRef, Assignment, Alignas ...
                raise Exception("Types that should not appear: " + \
                    str(node.type)
                    )

        # Process TypeDecl.
        elif(isinstance(node, pyc.c_ast.TypeDecl)):
            c_obj_type, c_obj_array_layers, c_obj_pointer_layers = \
                self._get_nesting_type(node)

        # Process Typename.
        elif(isinstance(node, pyc.c_ast.Typename)):
            # Get name.
            c_obj_name = node.name
            c_obj_quals = node.quals
            # TODO: align
            if(isinstance(node.type, pyc.c_ast.TypeDecl)):
                c_obj_type, c_obj_array_layers, c_obj_pointer_layers = \
                    self._get_nesting_type(node)
            else:
                raise Exception("TODO, node: " + str(node))

        elif(isinstance(node, pyc.c_ast.EllipsisParam)):
            raise self.EllipsisParamException("EllipsisParam is not supported \
                temporarily.")

        else:
            raise TypeError("Should not appear other types, node: " + str(node))

        if(is_function):
            return CFunc(
                c_obj_name, c_obj_quals, c_obj_storage, c_obj_funcspec, 
                c_obj_type, c_obj_array_layers, c_obj_pointer_layers, 
                c_obj_params
                )
        else:
            return CObj(
                c_obj_name, c_obj_quals, c_obj_align, c_obj_storage, 
                c_obj_type, c_obj_array_layers, c_obj_pointer_layers
                )


    def _get_nesting_type(self, node) -> list:
        """
        # Description:
            Get the real type nested by array and pointer.
        
        # Return:
            list in [ c_obj_type, c_obj_array_layers, c_obj_pointer_layers ]
        """
        c_obj_array_layers = 0
        c_obj_pointer_layers = 0
        
        # Get nesting levels.
        child_node = node
        while(isinstance(child_node, pyc.c_ast.ArrayDecl)):
            c_obj_array_layers += 1
            child_node = child_node.type
        while(isinstance(child_node, pyc.c_ast.PtrDecl)):
            c_obj_pointer_layers += 1
            child_node = child_node.type

        if(isinstance(child_node, pyc.c_ast.Typename)):
            child_node = child_node.type

        if(isinstance(child_node, pyc.c_ast.TypeDecl)):
            parent_type = child_node.type
            if(isinstance(parent_type, pyc.c_ast.Struct)):
                return [ "struct " + parent_type.name, c_obj_array_layers, 
                    c_obj_pointer_layers
                    ]
            elif(isinstance(parent_type, pyc.c_ast.IdentifierType)):
                return [ parent_type.names[0], c_obj_array_layers, 
                    c_obj_pointer_layers 
                    ]
            else:
                # TODO: pyc.c_ast.Union
                raise Exception("Unknown type in TypeDecl: " + str(parent_type))

        raise Exception("Unknown type: " + str(node))


    class ParserNotImplementedError(NotImplementedError):
        def __init__(self, *args):
            self.args = args


    class EllipsisParamException(ParserNotImplementedError):
        def __init__(self, *args):
            self.args = args


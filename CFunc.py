from .CObj import CObj

class CFunc(CObj):
    def __init__(self, name : str, quals : list, storge : list, 
        funcspec : list,return_type : str, 
        array_layers : int, pointer_layers : int, 
        params : list
        ) -> None:
        """
        # Description:
            Constructor of CFunc.
            
        # Parameters:
            name: 
                The name of the function.
            quals: 
                List of qualifiers (const, volatile).
            storage: 
                List of storage specifiers (extern, register, etc.).
            funcspec: 
                Function specifiers, (i.e. inline in C99 and _Noreturn_ in C11).
            return_type: 
                The real return type of the function.
            pointer_layers: 
                The number of pointer layers.
            params: 
                The arguments of the function.
        """
        super().__init__(name=name, quals=quals, align="", storage=storge, 
            real_type=return_type, array_layers=array_layers, 
            pointer_layers=pointer_layers
        )
        ############################## public  ##############################
        self.funcspec = funcspec
        self.return_type = return_type
        self.params = params


    def __str__(self) -> str:
        return self.to_str(True)


    def funcspec_to_str(self) -> str:
        """
        # Description:
            Output funcspec of function as str.
        
        # Return:
            The funcspec as str.
        
        # Example:
            for CFunc `func` in `inline _Noreturn void func();` :
                funcspec_to_str() -> "inline _Noreturn"
        """
        return " ".join(self.funcspec)


    def params_to_str(self) -> str:
        """
        # Description:
            Output params of function as str.

        # Return:
            The params as str.

        # Example:
            for CFunc `func` in `void func(int a, char b[]);` :
                params_to_str() -> "int a, char b[]"
            
            # TODO:
            # for CFunc `func` in `void func(int, char);` :
            #     params_to_str() -> "int param1, char param2"
        """
        params = []
        for param in self.params:
            params.append(param.to_str(semicolon = False, with_array = True))
        return ", ".join(params)


    def to_str(self, semicolon : bool = False) -> str:
        """
        # Description:
            Output the declaration of the function.

        # Parameters:
            semicolon: 
                Whether to add semicolon at the end of the declaration.
            
        # Return:
            The declaration of the function as str.
        
        # Example:
            for CFunc `func` in `void func(int a, char b[]);` :
                to_str() -> "void func(int a, char b[]);"
        """
        decl = ""

        quals = self.quals_to_str()
        if(quals):
            decl = quals + " "
        
        storage = self.storage_to_str()
        if(storage):
            decl += storage + " "
        
        funcspec = self.funcspec_to_str()
        if(funcspec):
            decl += funcspec + " "
        decl = self.type_to_str() + " " + self.name_to_str(True) \
            + "(" + self.params_to_str() + ")"
        
        if(semicolon):
            decl += ";"
        return decl


    def get_return_type(self) -> str:
        """
        # Description:
            Output the return type of the function.

        # Return:
            The return type of the function.

        # Example:
            for CFunc `func` in `void func(int a, char b[]);` :
                get_return_type() -> "void"
        """
        return self.return_type

    
    def gen_func_call(self) -> str:
        """
        # Description:
            Generate the function call of the function.
        
        # Return:
            The function call of the function.

        # Example:
            for CFunc `func` in `void func(int a, char b[]);` :
                gen_func_call() -> "func(a, b);"
        """
        func_call = ""
        func_param = ""
        param_nums = len(self.params)
        for i in range(param_nums):
            if(i < param_nums - 1):
                if(self.params[i].type_to_str() != "void"):
                    func_param += self.params[i].name + ", "
            else:
                if(self.params[i].type_to_str() != "void"):
                    func_param += self.params[i].name        
        
        if(self.type_to_str() != "void"):
            func_call += self.type_to_str() + " ret = " + self.name \
                + "(" + func_param + ");"
        else:
            func_call += self.name + "(" + func_param + ");"

        return func_call

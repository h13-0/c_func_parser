class CObj:
    """
    # Description:
        This class is used to transfer the information in pyc.c_ast.Decl and 
            provide the corresponding string.
        It is only applicable to type declaration and not suitable for detailed 
            definition (such as bitsize in struct).
    # Methods:
        get_name:   Get the name of the object.
    """
    def __init__(self, name : str, quals : list, align : list, storage : list, 
        real_type : str, array_layers : int, pointer_layers : int) -> None:
        """
        # Description:
            Constructor of CObj.
            
        # Parameters:
            name:           The name of the object.
            quals:          List of qualifiers (const, volatile).
            align:          Byte alignment.
                #Note: There are two cases:
                    _Alignas(2) int a;
                    _Alignas(char) int a;
            storage:        List of storage specifiers (extern, register, etc.).
            real_type:      The real type of the object.
            pointer_layers: The number of pointer layers.
            array_layers:   The number of array layers.
        """
        ############################## public  ##############################
        self.name = name
        self.quals = quals
        self.align = align
        self.storage = storage
        self.type = real_type
        self.array_layers = array_layers
        self.pointer_layers = pointer_layers


    def __str__(self) -> str:
        return self.to_str() # Just in default case.


    def type_to_str(self, 
        space_before_ptr : bool = True, 
        array_as_ptr : bool = False
        ) -> str:
        """
        # Description:
            Output type as str.

        # Parameters:
            space_before_ptr:  
                Whether to add space before pointer symbol(*).
            array_as_ptr:
                Whether to treat array as pointer.
        
        # Return:
            The type as str.

        # Example:
            for CObj `a` in `void *a[];` :
                type_to_str(False, False) -> "void*"
                type_to_str(True, False)  -> "void *"
                type_to_str(True, True)   -> "void **"
        """
        type_str = self.type
        pointer_layers = self.pointer_layers
        if(array_as_ptr):
            pointer_layers += self.array_layers

        if(pointer_layers):
            if(space_before_ptr):
                type_str += " "
            for i in range(pointer_layers):
                type_str += "*"
        return type_str


    def quals_to_str(self) -> str:
        return " ".join(self.quals)


    def align_to_str(self) -> str:
        return " ".join(self.align)


    def storage_to_str(self) -> str:
        return " ".join(self.storage)


    def name_to_str(self, with_array : bool = False) -> str:
        """
        # Description:
            Output c obj name as str.

        # Parameters:
            with_array:
                Whether to add array declaration.
        
        # Return:
            The c obj name as str.

        # Example:
            for CObj `a` in `void *a[];` :
                name_to_str(False) -> "a"
                name_to_str(True)  -> "a[]"
        """
        if(with_array):
            name = self.name
            for i in range(self.array_layers):
                name += "[]"
            return name
        else:
            return self.name


    def to_str(self, 
        space_before_ptr : bool = True,
        array_as_ptr : bool = False,
        space_after_ptr : bool = False,
        semicolon : bool = False, 
        with_array : bool = False
        ) -> str:
        """
        # Description:
            Output c obj declaration as str.

        # Parameters:
            space_before_ptr:  
                Whether to add space before pointer symbol(*).
            array_as_ptr:
                Whether to treat array as pointer.
            semicolon:  
                Whether to add semicolon at the end.
            with_array: 
                Whether to add array declaration.

        # Return:
            The c obj declaration as str.

        # Example:
            for CObj `a` in `void *a[];` :
                # When the default parameters are all default:

                to_str(space_before_ptr = True)  -> "void *a"  # default.
                to_str(space_before_ptr = False) -> "void*a"

                to_str(array_as_ptr = True)      -> "void **a"
                to_str(array_as_ptr = False)     -> "void *a"  # default.

                to_str(space_after_ptr = True)   -> "void * a"
                to_str(space_after_ptr = False)  -> "void *a"  # default.

                to_str(semicolon = True)         -> "void *a;"
                to_str(semicolon = False)        -> "void *a"  # default.

                to_str(with_array = True)        -> "void *a[]"
                to_str(with_array = False)       -> "void *a"  # default.
            
        # Note:
            Improper configuration will result in incorrect results:
                for CObj `a` in `void *a[];` :
                    to_str(True, True, True, True)   -> "void ** a[];" # Wrong.
        """
        decl = ""
        quals = self.quals_to_str()
        if(quals):
            decl += quals + " "
        
        align = self.align_to_str()
        if(align):
            decl += align + " "
        
        storage = self.storage_to_str()
        if(storage):
            decl += storage + " "
        
        type_ = self.type_to_str(
            space_before_ptr = space_before_ptr, 
            array_as_ptr = array_as_ptr
        )

        name = self.name_to_str(with_array=with_array)

        if(type_ != "void"):
            if(type_.endswith("*") and not space_after_ptr):
                    decl += type_ + name
            else:
                decl += type_ + " " + name
        else:
            decl += self.type_to_str()

        if(semicolon):
            decl += ";"
        return decl    

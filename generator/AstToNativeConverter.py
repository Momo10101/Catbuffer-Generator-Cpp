import lark
import sys

from catparser import ast



def ast_to_native( type_descriptors ):
    """
    Takes type descriptors directly from the catbuffer schema and converts 
    it to input for the C++ generator. The output of this function
    can be passed directly to 'convert()' in '__main__.py' to 
    generate C++ code.
    """

    print("\n\nConvert from AST to native generator format ----------------")

    aliases       = list()
    structs       = list()
    abstracts     = set()
    enums         = dict()  
    factory_enums = dict()  
    enum_to_type  = dict()  # stores the types of enums (uint16, unit32, etc)


    # Enum conversion -----------------------------------------------
    print("\n  - Convert enums types:")
    for idx, model in enumerate( type_descriptors ):

        if isinstance( model, ast.Enum ):
            print( "\t"+str(idx)+": "+str(type(model))+" -> "+model.name )

            # enum header
            enum         = dict()
            enum["name"] = model.name
            enum["type"] = "enum " + model.base.short_name.value
            values       = list()

            if model.comment:
                enum["comment"] = model.comment.parsed

            # store type for later use
            enum_to_type[model.name] = model.base.short_name.value

            # save enum values
            for value in model.values:
                tmp = dict()
                tmp["name"]  = value.name
                tmp["value"] = value.value
                if value.comment:
                    tmp["comment"] = value.comment.parsed

                values.append(tmp)

            enum["values"] = values

            enums[model.name] = enum


    # Alias conversion -----------------------------------------------
    print("\n  - Convert alias types:")
    for idx, model in enumerate(type_descriptors):

        if isinstance(model, ast.Alias ):
            print( "\t"+str(idx)+": "+str(type(model))+" -> "+model.name )

            if( isinstance(model.linked_type, ast.FixedSizeBuffer) ):
                alias = { "name": model.name, 
                          "size": model.linked_type.size, 
                          "type": "alias " + "array uint8" }

            elif( isinstance(model.linked_type, ast.FixedSizeInteger) ):
                alias = { "name": model.name, 
                          "type": f"alias {model.linked_type.short_name}" }

            else:
                print( "Error: Unknown alias linked_type in AST model!" )
                exit(1)

            aliases.append(alias)


    # Struct conversion -----------------------------------------------
    print("\n  - Convert struct types:")
    for idx, model in enumerate(type_descriptors):

        if isinstance(model, ast.Struct):
            print( "\t"+str(idx) + ": " + str(type(model)) + " -> " + model.name )

            layout = []
            sizeof = dict()

            for idx, field in enumerate(model.fields):

                if( field.name == "TRANSACTION_VERSION" or field.name == "TRANSACTION_TYPE" ):
                    continue

                tmp = dict()
                tmp["name"] = field.name
                if field.comment:
                    tmp["comment"] = field.comment.parsed

                # builtin field type ---------------------------------------------------------
                if isinstance(field.field_type, ast.FixedSizeInteger):
                   
                    if field.disposition == None:
                        disposition = ""
                    elif field.disposition in ["const", "reserved"]:
                        disposition  = field.disposition
                        tmp["value"] = field.value
                    elif field.disposition == "sizeof":
                        disposition  = ""
                        sizeof[field.value] = field.name
                    else:
                        print(f"Error: Disposition '{field.disposition}' unknown for field '{field.name}' in AST model!")
                        exit(1)

                    tmp["type"] = f'{disposition} {field.field_type.short_name.value}'


                # user defined field type ----------------------------------------------------
                elif isinstance(field.field_type, lark.Token):

                    if field.field_type.type == "USER_TYPE_NAME":

                        if field.field_type.value in abstracts:
                            tmp["size"]                 = sizeof[field.name]
                            tmp["type"]                 = f"array_sized {field.field_type.value}"
                            tmp["header_type_field"]    = "type"      #TODO: hard coded
                            tmp["header_version_field"] = "version"
                        else:
                            tmp["type"] = field.field_type.value

                    else:
                        print(f'Error: Unknown field type {field.field_type.type} in AST model for field {field.name}')
                        exit(1)


                # array field type ----------------------------------------------------
                elif isinstance(field.field_type, ast.Array):

                        if(field.field_type.disposition == "array fill"):
                            tmp["type"] = f'array_fill {field.field_type.element_type}'

                        elif(field.field_type.disposition == "array"):
                            tmp["type"] = f'array {field.field_type.element_type}'
                            tmp["size"] = field.field_type.size

                        elif(field.field_type.disposition == "array sized"):
                            tmp["type"]                 = f'array_sized {field.field_type.element_type}'
                            tmp["size"]                 = field.field_type.size
                            tmp["header_type_field"]    = "type"    # model.discriminator[0]
                            tmp["header_version_field"] = "version"

                            if field.field_type.alignment:
                                tmp["align"] = field.field_type.alignment

                        else:
                            print( f'Error: Unknown array field {field.field_type.disposition} for field {field.name}' )
                            exit(1)

                else:
                    print( f'Error: Unknown struct field:\n{idx}: {field}' )
                    exit(1)


                # add conditional
                if isinstance(field.value, ast.Conditional) and field.value.operation != "in":
                    tmp["condition"]           = field.value.linked_field_name
                    tmp["condition_operation"] = field.value.operation
                    tmp["condition_value"]     = field.value.value


                layout.append(tmp)


            # if struct is not abstract, set its type and version
            if model.disposition != "abstract" and model.discriminator:

                discriminator = dict()

                for init in model.initializers:
                    if init.target_property_name == "type":                        
                        for field in model.fields: # find variable in fields which gives struct its type
                            if field.name == init.value:
                                discriminator_enum          = field.field_type.value
                                discriminator["type"]       = f'struct_type {model.factory_type+"Group"}'
                                discriminator["value"]      = field.value
                                discriminator["type_field"] = "type"
                                discriminator["header"]     = model.factory_type
                                
                    elif init.target_property_name == "version": # find variable in fields which gives struct its version
                        for field in model.fields:
                            if field.name == init.value:
                                struct_version = field.value
                                discriminator["version_field"] = "version"

                if "value" in discriminator:
                    discriminator["value"] = discriminator["value"] + f' @{struct_version}'

                    # create a new internal enum (if not created yet)
                    if model.factory_type+"Group" not in factory_enums:
                        fac_enum = {}
                        fac_enum["name"]   = model.factory_type+"Group"
                        fac_enum["type"]   = "enum " + enum_to_type[discriminator_enum]
                        fac_enum["values"] = []
                        factory_enums[ model.factory_type+"Group" ] = fac_enum

                    tmp_enum = dict()
                    tmp_enum["name"] = discriminator["value"].split()[0]

                    for enum in enums[discriminator_enum]["values"]:
                        if enum["name"] == tmp_enum["name"]:
                            tmp_enum["value"] = enum["value"]


                    # check that enum was not added before (this can happen if there are more than one version of a struct)
                    unique = True
                    for enum in factory_enums[ model.factory_type+"Group" ]["values"]:
                        if enum["name"] == tmp_enum["name"]:
                            unique = False
                            break

                    # add enum if unique
                    if unique:
                        factory_enums[ model.factory_type+"Group" ]["values"].append(tmp_enum)

                else:
                    print(f'ERROR: Did not find type or version field for struct "{model.name}"!')
                    exit(1)

                layout.append(discriminator)

            
            if model.disposition == "abstract":
                abstracts.add(model.name)
                for field in layout:
                    if field["name"] == "type":
                        field["type"] = model.name+"Group"


            # create struct and save
            struct = dict()
            struct["name"]   = model.name
            struct["type"]   = "struct"
            struct["layout"] = layout
            
            if model.comment:
                struct["comment"] = model.comment.parsed

            structs.append(struct)


        elif isinstance( model, ast.Enum ) or isinstance(model, ast.Alias ):
            continue
        else:
            print( "Error: Unknown type" )
            exit(1)

    for key, value in factory_enums.items():
        enums[key] = value


    print("\n\tConversion done!\n\n")

    return (aliases + list(enums.values()) + structs)
    

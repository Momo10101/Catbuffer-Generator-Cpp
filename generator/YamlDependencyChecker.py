import typing
from enum import Enum, auto


class YamlDependencyCheckerResult(Enum):
    OK                                  = auto()  # Everything went well
    ARRAY_SIZED_HEADER_NOT_DECLARED     = auto()
    ARRAY_SIZED_TYPE_FIELD_NOT_DECLARED = auto()


class YamlDependencyChecker():
       
    @staticmethod
    def array_sized( class_name, field: dict, class_decl: dict ) -> typing.Tuple[ YamlDependencyCheckerResult, str ]:

        header = field["type"]
        if header not in class_decl:
            return YamlDependencyCheckerResult.ARRAY_SIZED_HEADER_NOT_DECLARED, f"\n\nError: The header '{header}' in array_sized '{field['name']}' not declared (error detected for array_sized field '{field['name']}' in struct '{class_name}')!\n\n"

        decl = class_decl[header]

        header_field = field["header_type_field"]
        if header_field not in decl.member_vars:
            return YamlDependencyCheckerResult.ARRAY_SIZED_TYPE_FIELD_NOT_DECLARED, f"\n\nError: The field '{header_field}' in '{header}' not declared (error detected for array_sized field '{field['name']}' in struct '{class_name}')!\n\n"

        return YamlDependencyCheckerResult.OK, ""










#        # check cond var has been defined #TODO: Disabled for now. Enable when adding Enums
#        if cond_var not in self.member_vars:
#            return DeclGenResult.CONDITION_VAR_NOT_DEFINED, f"\n\nError: Condition variable '{cond_var}' not defined in struct '{self.class_name}'!\n\n"

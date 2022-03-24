Catbuffer C++ Generator
=======================

A simple C++ code generator for serializing and deserializing Catbuffer schemas.

![img](https://pbs.twimg.com/media/B8AZgE-CUAAIB4a.jpg)


<!-- toc -->
* [Overview](#overview)
  * [Instructions](#instructions)
  * [Repository Structure](#repository-structure)
  * [Testing](#testing)
  * [Prettyprinting](#prettyprinting)
* [YAML Input File Format](#yaml-input-file-format)
  * [Builtin Data Types](#builtin-data-types)
  * [Custom Data Types](#custom-data-types)
  * [Defining Enumeration](#defining-enumeration)
  * [Defining Structs](#defining-structs)
    * [Builtin Type Field](#builtin-type-field)
    * [Custom Type Field](#custom-type-field)
    * [Condition Field](#condition-field)
    * [Reserved Field](#reserved-field)
    * [Inline Field](#inline-field)
    * [Const Field](#const-field)
    * [Array Field](#array-field)
    * [Array Sized Field](#array-sized-field)
    * [Array Fill Field](#array-fill-field)
* [Generator code](#generator-code)
* [C++ generated files](#c-generated-files)
  * [ICatBuffer interface](#icatbuffer-interface)
  * [RawBuffer](#rawbuffer)
<!-- tocstop -->


# Overview

Catbuffer is a very simple and memory efficient data serialization format. No extra information or padding is read or written, apart from what is defined by the user.
Catbuffer is the serialization mechanism originally developed for the Symbol blockchain to serialize and deserialize data structures for sending and receiving data between network clients. It consist of three components. The **catbuffer-schema**, which is the interface description language (IDL) used to define the data structures; The **catbuffer-parser** which parses the schemas and generates a .yaml output file; The **catbuffer-generator** which takes the generated .yaml file as input and generates C++ files which are compiled into a library. The process is shown below: 

**catbuffer-schema** --> **catbuffer-parser** --> .yaml file --> **catbuffer-generator** --> .cpp/.h files --> C++ lib file

Note that it is possible to define data structures directly in YAML format instead of catbuffer schemas, however, using schemas is more human readable and less verbose to write. 

Below is shown a simple Catbuffer schema:

```c++
struct Coordinate
	x = uint32
	y = uint32
	z = uint32
```

The generated code will allow serialization and manipulation of the above data structure in C++ like so:

```c++
  // Read vector 'a' (deserialize from file)
  RawBuffer dataA = read_file( "vector_a.raw" ); // read_file returns a raw byte buffer
  Coordinate a;
  a.Deserialize( dataA );  // 'Deserialize()' initializes 'Coordinate' members from a raw buffer

  // Read vector 'b' (deserialize from file)
  RawBuffer dataB = read_file( "vector_b.raw" );
  Coordinate b;
  b.Deserialize( dataB );

  // Compute cross product (initialize 'Coordinate' Catbuffer 'c')
  Coordinate c;
  c.x = a.y*b.z − a.z*b.y; 
  c.y = a.z*b.x − a.x*b.z;
  c.z = a.x*b.y − a.y*b.x;

  // Write vector 'c' (serialize to file)
  RawBuffer dataC;
  c.Serialize( dataC ); // 'Serialize()' writes 'Coordinate' members to a raw buffer
  write_file( dataC, "vector_c.raw" );
```


## Instructions

To generate the library file, do the following:


1. Clone the ``catbuffer-generators`` repository:

```bash
git clone https://github.com/Momo10101/Catbuffer-Generator-Cpp
```

2. Generated the .cpp/.h files:

```bash
python3 -m generator input_file.yaml output_directory/
```

3. Enter the 'output_directory' where files have been generated:

```bash
cd output_directory
```

4. Create a directory to build library:

```bash
mkdir _build && cd _build
```

5. Generate CMake files:

```bash
cmake ..
```

6. Compile library

```bash
make
```

You should now see a file called **libcatbuffer.a** which you can link to you program in order to serialize/deserialize the data structures you defined in your schemas or .yaml file.


## Repository Structure

* **[`generator`](generator/)**: The python source code for parsing an input YAML file and outputting C++ code.
* **[`cpp_source`](cpp_source/)**: Static C++ source code needed for serialization/deserialization, which is independent of an input YAML file.
* **[`cpp_build_files`](cpp_build_files/)**: C++ build files for compiling the code generated by the generator.
* **[`unit_tests`](unit_tests/)**: Unit tests to test the code in the **generator/** folder.
* **[`yaml_test_inputs`](yaml_test_inputs/)**: YAML input files for testing.
* **[`test_vectors`](test_vectors/)**: test vector corresponding to the yaml test inputs in the **yaml_test_inputs/** folder.
* **[`end_to_end_test`](end_to_end_test/)**: Contains end to end tests where serialized inputs are deserialized and then serialized again to check that the output is equal to the input. The test takes the yaml inputs in the 'yaml_test_inputs' folder, generates C++ outputs, takes the test vectors in 'test_vectors', uses the generated code to deserialize input vectors and then serializes again to compare the result with the initial input vectors.


## Testing

The generator includes multiple unit tests located in the **unit_tests** folder. They can be run by using **'python3 -m unittest'** like so:

```bash
python3 -m unittest -v unit_tests/TestYamlDependencyErrorDetection.py
```

To test the correct deserializtion/serialization of the generated code, some yaml input tests are included in the folder **yaml_test_inputs**. To run these test run the the following commands while at the base folder:

```bash
mkdir output-symbol
python3 -m generator yaml_test_inputs/symbol-all-transactions.yaml output-symbol

cd output-symbol
mkdir _build && cd _build
cmake ..
make

cd ../../end-to-end-tests
mkdir _build && cd _build
cmake ..
make

./main
```

[//]: # (TODO: Add script for the above and add automatic fuzzer test and valgrind check also)


## Prettyprinting
The generator also supports generating optional C++ code for printing out deserialized data. It is also possible to generate a command line interface (cli) for deserializing raw files and hex strings. To add support for prettyprinting and cli, use the '--generate-print' option:

```bash
python3 -m generator input_file.yaml output_directory --generate-print
```

This will add a 'Print()' method to the 'ICatbuffer' interface and an executable called 'cmd' which can be used to deserialize hex strings and raw files like so:

```bash
$./cmd --hex Coordinate 0D0000000E0000000F000000
Coordinate (12 bytes)
{
	uint32_t x: 13 (4 bytes)
	uint32_t y: 14 (4 bytes)
	uint32_t z: 15 (4 bytes)
}

Data deserialized successfully!

```


# YAML Input File Format

The generator accepts YAML files and outputs C++ files. An example of a simple data structure defined in YAML is shown below:

```yaml
- name: Coordinate
  type: struct
  comments: a structure for storing a 3D coordinate
  
  layout:
  - name: x
    type: int32
    comments: the x coordinate

  - name: y
    type: int32
    comments: the y coordinate
  
  - name: z
    type: int32
    comments: the z coordinate
```

The above markup defines a structure called **Coordinate** with 3 fields called *x*, *y* and *z* of type *int32*. Note that the comment fields are optional.


## Builtin Data Types

Catbuffer supports the following builtin datatypes: 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64'

[//]: # (TODO: we should add support for float and double as well)

## Alias Data Types

Apart from the builtin types, alias types can be defined like so:

```yaml
- name: FeeMultiplier
  type: uint16
```

or

```yaml
- name: Address
  size: 24
  type: array uint8
```

In C++, the above two examples would be equivalent to:

```c++
using BlockFeeMultiplier = uint32_t;
```
and 

```c++
using Address = struct Address_t { uint8_t data[24]; };
```

Custom types can be useful for type checking and can be used when defining structs.


## Defining Enumeration

An enum can be defined like so:

```yaml
- name: NetworkType
  comments: enumeration of network types
  type: enum uint8

  values:
  - name: MAINNET
    comments: public network
    value: 104
    
  - name: TESTNET
    comments: public test network
    value: 152
```

which would be equivalent to this in C++:


```c++
/**
 * enumeration of network types
 */
enum class NetworkType : uint8_t
{
	MAINNET = 104, //< public network
	TESTNET = 152, //< public test network
};
```

## Defining Structs

Structs are the most elaborate custom defined types in Catbuffer and can contain multiple fields including other structs. A struct has to define at least three keys: 'name', 'type' and 'layout'. An optional 'comment' key can also be added. The 'type' key has to be set to 'struct' and 'layout' defines the fields in the struct. An example of a 'struct' was shown [here](#yaml-input-file-format). There are in total 9 field types that can appear inside 'layout'. They are listed below:

*builtin type*

*alias type*



*condition*

*reserved*

*const*

*inline*



*array*

*array_sized*

*array_fill*


The subsections below will explain the above field types in more detail.


### Builtin Type Field

Builtin types are the simplest types supported in Catbuffer:

```yaml
- name: time_elapsed
  type: uint64

- name: address
  type: array uint8
```


### Custom Type Field

Some custom types such as **NetworkType**, **FeeMultiplier**, **Coordinate** were defined [here](#defining-enumeration), [here](#alias-data-types) and [here](#yaml-input-file-format). Below they are shown as fields in a struct:

```yaml
- name: network
  type: NetworkType
 ```
 
```yaml
- name: multiplier
  type: FeeMultiplier
```

```yaml
- name: coordinate
  type: Coordinate
```



### Condition Field

Condition fields can be used to add optional fields. If a condition is met then then field is serialized, otherwise it is ignored. Below is an example of a condition field:

```yaml
- name: msg
  type: Message
  condition: message_included
  condition_operation: not equals
  condition_value: 0
```

The name of the field is 'msg' and is of alias type 'Message'. It is only serialized/deserialized if **message_included != 0**. Note that **message_included** has to be a field in the same struct, defined before 'msg'. The only condition operations supported at the moment are **equals** and **not equals**.

[//]: # (#TODO: add support for other condition operators and perhaps change names to '=', '!=', '<=', '=>' etc.)

### Reserved Field

Reserved fields are useful for when a field is reserved for future use and should have a specific value that can not be set by the user. It is also useful for adding padding. Reserved fields are defined like [builtin](#builtin-type-field) fields but with the keyword **reserved** added to the type field and a value field. Below is an example of how to define a reserved field for padding:

```yaml
  - name: padding
    type: reserved uint32
    value: 0
    comments: reserved padding to align next field on 8-byte boundary
```

Note that when serializing/deserializing, if the value read for a reserved field does not equal the **value** key, it is considered an error and the serialization/deserialization will fail.


### Inline Field

Inline fields can be used to inline structs into other structs, so that instead of doing *OuterStruct.InnerStruct.my_variable*, one can do *OuterStruct.my_variable*. An example of how to do an inline field is shown below

```yaml
  - type: inline Coordinate
```


### Const Field

It is possible to define constants in Catbuffer. Although they are not read or written when serializing, they are included as class members when generating code. They can be defined like so:

```yaml
- name: VERSION
  type: const unit8
  value: 14
```

Which would generate a C++ class member similar to this:

```c++
const uint8_t VERSION = 14;
```


### Array Field
An array field is just a normal fixed size array with elements of a fixed size.

```yaml
  - name: amounts
    size: amount_size
    type: array uint64
```

Note that **amount_size** has to be a field in the same struct which appears before the array field. Furthermore, note that **type** can also be a struct defined type, but the size of each array element must be the same for all elements, which means that they can not contain arrays of different sizes for example. Finally note that if the same size field is used for multiple arrays, the arrays have to be of equal size when serializing/deserializing 

[//]: # (TODO: add check and unit test)
[//]: # (TODO: add support for int instead of variable)

### Array Sized Field

An **array_sized** field is an array where the number of elements is not known, but where the total array size in bytes is known. This is useful for arrays where each element is of a different type and size. The array elements in this case are of user defined custom types, however, all elements must share a common header field, which in turn contains a field which indicates what the element type is. The header type is indicated with the **header** key and the field within the header containing the element type, is indicated with the **header_type_field** key. An example of this is shown below:

```yaml
  - name: transactions
    size: payload_size
    header: array_sized EmbeddedTransaction #<--- Header common to all elements in array.
    header_type_field: elem_type            #<--- Name of field in 'EmbeddedTransaction' which contains type of element.
    align: 8                                #<--- Optional alignment of array elements in bytes.
```

In the above example the total size of the array in bytes is given in the **size** key. '**EmbeddedTransaction**' is the header which is common to all elements in the '**transactions**' array. The field in the '**EmbeddedTransaction**' which indicates the type of an element is called '**elem_type**'. The type of the '**elem_type**' field itself has to be an enum. An optional alignment for the array elements can be indicated by specifying an **align** field. This will add padding at the end of each array element so that the subsequent element is memory aligned. If alignment is specified then the **size** field must includes the size of the paddings.

Given an **array_sized** field, Catbuffer will automagically know how to serialize and deserialize. For this to happen, the elements in the array also need to be defined with a specific field called **struct_type** as shown below: 

```yaml
  - type: struct_type TransactionType  #<---'TransactionType' is an Enum defined somewhere else.
    value: MOSAIC_DEFINITION @3        #<--- MOSAIC_DEFINITION is an Enumerator in 'TransactionType', and '@3' is the version.
    header: EntityBody                 #<--- header where version and type of struct is stored.
    version_field: version             #<--- the name of the field within the header defining the version.
    type_field: type                   #<--- the name of the field within the header defining the type.
```

**MOSAIC_DEFINITION** is an enumerator in the **TransactionType** enum, which also has to be the type of the **elem_type** field mentioned above. This enum gives the type of the struct within the group **TransactionType**. The **@3** part indicates the version of the struct. This way Catbuffer can support evolving structures over time.


[//]: #( TODO: header, version_field and type_field should not be defined here since its the same for all structs of type TransactionType )
[//]: #( TODO: what should happen if a version and type combination does not exist? )
[//]: #( TODO: We need to think about this a bit more. What if there are two fields of type EmbeddedTransaction? What if its not inline? )



### Array Fill Field

An 'array fill' is a normal array with fixed sized elements, but where the number of elements is computed based on how much data is still pending to be serialized/deserialized. So for example if the total amount of data to deserialize is 'n' bytes and 'm' bytes of data is still pending to be serialized, then the size of the array is 'n-m' bytes. An 'array fill' field is defined like so:

```yaml
  - name: signatures
    type: array_fill Signature
```

Note that an 'array fill' field has to be the last field in the outermost struct, otherwise it is an error.

[//]: #(TODO: implement check)


# Generator code
----------------
The generator code, defined in the **generator/** folder, contains multiple classes to convert YAML inputs to C++ code. There are two types of classes, the ones that generate C++ declaration code which goes into .h files and definition code which goes into .cpp files. Below is a quick overview of the main classes:


|Declaration Classes           | Description                                                                                     | 
|------------------------------|-------------------------------------------------------------------------------------------------|
|CppClassMemberGenerator       | Takes fields defined in YAML and converts them to C++ class members.                            |
|CppClassDeclarationGenerator  | Generates C++ class declarations which go into **.h** files.                                    |
|CppTypesGenerator             | Converts enums and alias types defined in YAML and outputs them in **types.h**.                 |


|Definition Classes            | Description                                                                                     |
|------------------------------|-------------------------------------------------------------------------------------------------|
|CppSerializationGenerator     | Takes a field defined in YAML and generates C++ code to serialize it into a raw byte buffer.    |
|CppDeserializationGenerator   | Takes a field defined in YAML and generates C++ code to deserialize it from a raw byte buffer.  |
|CppClassDefinitionGenerator   | Generates C++ class definitions which go into **.cpp** files.                                   |
|CppEnumeratorToClassGenerator | Generates C++ functions to convert from enums to class instances.                               |


|Yaml Checker Classes          | Description                                                                                     |
|------------------------------|-------------------------------------------------------------------------------------------------|
|YamlFieldChecker              | Contains checks to ensure that the different fields contain the necessary YAML keys             |
|YamlDependencyChecker         | Contains checks to ensure that the dependencies defined in the YAML fields are valid            |

The above classes are documented in more detail in the source code.


# C++ generated files
---------------------
When done parsing a YAML input file, three different C++ files are generated. First a **types.h** file is generated, which contains all simple custom types and enums. Then for each defined struct type, C++ class files are generated in **.cpp/.h**, which contain the defined fields as class members and implement the ICatbuffer interface which enable serialization/deserialization. The ICatbuffer interface is explained below. Lastly the files **converters.h/.cpp** contain the functions necessary to convert an enumerator to an instance of a struct (represented as an ICatbuffer pointer) as explained [here](#array-sized-field).


## ICatBuffer interface
The ICatBuffer interface declares methods for serializing and deserializing raw byte buffers. It also declares a method for getting the total size of all fields in serialized form. All structs declared in the input YAML file are converted to C++ classes that inherit from ICatbuffer. This allows structs to be initialized by deserialization. The 'ICatBuffer.h' header file is defined in the **cpp_source/** folder.


## RawBuffer
Rawbuffer is the buffer which is declared in the ICatBuffer interface as input for the serializer and deserializer methods. It is therefore compiled and added in the output C++ library file. Rawbuffer implements a simple buffer handling functionality with out of bounds protection.

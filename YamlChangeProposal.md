```yaml
# new

- name: SizePrefixedEntity
  type: struct
  comments: binary layout for a size-prefixed entity

  layout:
  - name: size
    type: uint32
    comments: entity size


- name: VerifiableEntity
  type: struct
  comments: binary layout for a verifiable entity

  layout:
  - comments: reserved padding to align Signature on 8-byte boundary
    name: verifiable_entity_header_reserved_1
    type: reserved uint32
    value: 0
    # TODO: Some questions: Should reserved fields always have a value? Should reserved fields appear as class members? Should a user be able to set it?

  - name: signature
    type: Signature
    comments: entity signature


- name: EntityBody
  type: struct
  comments: binary layout for a blockchain entity (block or transaction)

  layout:
  - name: signer_public_key
    type: PublicKey
    comments: entity signer's public key

  - comments: reserved padding to align end of EntityBody on 8-byte boundary
    name: entity_body_reserved_1
    type: reserved uint32
    value: 0

  - comments: entity version
      name: version
      type: uint8
  
  - comments: entity network
      name: network
      type: NetworkType


- name: Transaction
  type: struct
  comments: binary layout for a transaction

  layout:
  - type: inline SizePrefixedEntity
    comments: ''

  - type: inline VerifiableEntity
    comments: ''

  - type: inline EntityBody
    comments: ''

  - name: type
    type: TransactionType
    comments: transaction type

  - name: fee
    type: Amount
    comments: transaction fee

  - name: deadline
    type: Timestamp
    comments: transaction deadline



- name: AggregateTransactionBody
  type: struct
  comments: binary layout for an aggregate transaction

  layout:
  - name: transactions_hash
    type: Hash256
    comments: aggregate hash of an aggregate's transactions

  - name: payload_size
    type: uint32
    comments: transaction payload size in bytes \note this is the total number of
      bytes occupied by all sub-transactions

  - name: aggregate_transaction_header_reserved_1
    type: reserved uint32
    value: 0
    comments: reserved padding to align end of AggregateTransactionHeader on 8-byte
      boundary    

  - name: transactions
    size: payload_size                      # <--- Total size of array in bytes
    type: array_sized EmbeddedTransaction   # <--- EmbeddedTransaction in this case is the common header of all array elements
    type_field: type                        # <--- The name of the field within the header defining the 'type' of array element
    comments: sub-transaction data (transactions are variable sized and payload size
      is in bytes)

  - disposition: 
    name: cosignatures
    type: array_fill Cosignature
    comments: cosignatures data (fills remaining body space after transactions)


- name: NamespaceRegistrationTransactionBody
  type: struct
  comments: binary layout for a namespace registration transaction
  layout:
  
  - name: BlockNameUnion
    type: union
    switch: registration_type
    comments: ''
    layout:
    - name: duration
      type: BlockDuration
      case: ROOT
      comments: namespace duration

    - name: parent_id
      type: NamespaceId
      case: CHILD
      comments: parent namespace identifier

  - name: id
    type: NamespaceId
    comments: namespace identifier

  - name: registration_type
    type: NamespaceRegistrationType
    comments: namespace registration type

  - name: name_size
    type: uint8
    comments: namespace name size

  - name: name
    type: array uint8
    size: name_size
    comments: namespace name


- name: AggregateCompleteTransaction
  type: struct
  comments: binary layout for an aggregate complete transaction

  layout:
  - value: AGGREGATE_COMPLETE @1 # <--- The @ sign gives the version.
    header: EntityBody           # <--- Header where 'version' and 'type' of struct is stored
    version_field: version       # <--- The name of the field within the header defining the 'version'
    type_field: type             # <--- The name of the field within the header defining the 'type'

  - type: inline Transaction
    comments: ''

  - type: inline AggregateTransactionBody
    comments: ''

```




```yaml
# original

- comments: binary layout for a size-prefixed entity
  layout:
  - comments: entity size
    name: size
    signedness: unsigned
    size: 4
    type: byte
  name: SizePrefixedEntity
  type: struct


- comments: binary layout for a verifiable entity
  layout:
  - comments: reserved padding to align Signature on 8-byte boundary
    disposition: reserved
    name: verifiable_entity_header_reserved_1
    signedness: unsigned
    size: 4
    type: byte
    value: 0
  - comments: entity signature
    name: signature
    type: Signature
  name: VerifiableEntity
  type: struct


- comments: binary layout for a blockchain entity (block or transaction)
  layout:
  - comments: entity signer's public key
    name: signer_public_key
    type: PublicKey
  - comments: reserved padding to align end of EntityBody on 8-byte boundary
    disposition: reserved
    name: entity_body_reserved_1
    signedness: unsigned
    size: 4
    type: byte
    value: 0
  - comments: entity version
    name: version
    signedness: unsigned
    size: 1
    type: byte
  - comments: entity network
    name: network
    type: NetworkType
  name: EntityBody
  type: struct


- comments: binary layout for a transaction
  layout:
  - comments: ''
    disposition: inline
    type: SizePrefixedEntity
  - comments: ''
    disposition: inline
    type: VerifiableEntity
  - comments: ''
    disposition: inline
    type: EntityBody
  - comments: transaction type
    name: type
    type: TransactionType
  - comments: transaction fee
    name: fee
    type: Amount
  - comments: transaction deadline
    name: deadline
    type: Timestamp
  name: Transaction
  type: struct


- comments: binary layout for an aggregate transaction
  layout:
  - comments: aggregate hash of an aggregate's transactions
    name: transactions_hash
    type: Hash256
  - comments: transaction payload size in bytes \note this is the total number of
      bytes occupied by all sub-transactions
    name: payload_size
    signedness: unsigned
    size: 4
    type: byte
  - comments: reserved padding to align end of AggregateTransactionHeader on 8-byte
      boundary
    disposition: reserved
    name: aggregate_transaction_header_reserved_1
    signedness: unsigned
    size: 4
    type: byte
    value: 0
  - comments: sub-transaction data (transactions are variable sized and payload size
      is in bytes)
    disposition: array sized
    name: transactions
    size: payload_size
    type: EmbeddedTransaction
  - comments: cosignatures data (fills remaining body space after transactions)
    disposition: array fill
    name: cosignatures
    size: 0
    type: Cosignature
  name: AggregateTransactionBody
  type: struct


- comments: binary layout for an aggregate complete transaction
  layout:
  - comments: ''
    disposition: const
    name: TRANSACTION_VERSION
    signedness: unsigned
    size: 1
    type: byte
    value: 1
  - comments: ''
    disposition: const
    name: TRANSACTION_TYPE
    type: TransactionType
    value: AGGREGATE_COMPLETE
  - comments: ''
    disposition: inline
    type: Transaction
  - comments: ''
    disposition: inline
    type: AggregateTransactionBody
  name: AggregateCompleteTransaction
  type: struct


- comments: binary layout for a namespace registration transaction
  layout:
  - comments: namespace duration
    condition: registration_type
    condition_operation: equals
    condition_value: ROOT
    name: duration
    type: BlockDuration
  - comments: parent namespace identifier
    condition: registration_type
    condition_operation: equals
    condition_value: CHILD
    name: parent_id
    type: NamespaceId
  - comments: namespace identifier
    name: id
    type: NamespaceId
  - comments: namespace registration type
    name: registration_type
    type: NamespaceRegistrationType
  - comments: namespace name size
    name: name_size
    signedness: unsigned
    size: 1
    type: byte
  - comments: namespace name
    disposition: array
    element_disposition:
      signedness: unsigned
      size: 1
    name: name
    size: name_size
    type: byte
  name: NamespaceRegistrationTransactionBody
  type: struct

```

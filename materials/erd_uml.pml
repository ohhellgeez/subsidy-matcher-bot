@startuml
!theme plain
hide circle
skinparam linetype ortho
skinparam EntityBackgroundColor #f8f9fa
skinparam EntityBorderColor #343a40
skinparam EntityHeaderBackgroundColor #343a40
skinparam EntityHeaderFontColor white

entity "support_measures" as support_measures {
  * id : varchar <<PK>>
  --
  id_form : varchar
  active : int
  name : varchar(150)
  preview : varchar(250)
  short_description : text
  full_description : text
  start_date : timestamp
  end_date : timestamp
  support_type : int
  support_count : int
  support_amount_from : int
  support_amount_till : int
  recipient_category : varchar
}

entity "measure_requirements" as measure_requirements {
  * measure_id : varchar <<PK, FK>>
  --
  opf : varchar
  okwed : varchar
  not_okwed : varchar
  min_empl_amount : int
  max_empl_amount : int
  min_exist_term : int
  okato : varchar
  ukep : boolean
  scoring : boolean
}

entity "documents" as documents {
  * id : serial <<PK>>
  --
  * measure_id : varchar <<FK>>
  * link : varchar
  type : varchar(10)
  size : float
  * name : varchar
  description : text
}

entity "regions" as regions {
  * id : serial <<PK>>
  --
  * okato : varchar(20)
  * code : varchar(10)
  * name : varchar
  district : varchar
}

entity "companies" as companies {
  * inn : varchar(12) <<PK>>
  --
  * name : varchar
  * opf : varchar
  * okwed : varchar(10)
  employees_count : int
  exist_term_months : int
  * region_id : int <<FK>>
}

support_measures ||--|| measure_requirements : "1:1"
support_measures ||--o{ documents : "1:N"
regions ||--o{ companies : "1:N"

@enduml
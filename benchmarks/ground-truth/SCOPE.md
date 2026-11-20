# PetClinic human GT — labeling scope

Pin: `500158f732419217507c7656904b8e6aa1bcc0d6`

| Question | Answer for this label file |
| --- | --- |
| Production sources | **`src/main/java` only** for Direct / Indirect |
| Test sources | **Test link** (out of Direct/Indirect expects) |
| Method params / returns | **Yes** → `uses_type` |
| Generic type arguments (`Page<Vet>`, `List<Owner>`) | **No** (not in this label version) |
| Interfaces without method bodies | Inject/uses only where a signature still shows the type under the rules above; no body → no call edges |
| Class literals (`Person.class`) | **No** |
| Vocabulary for Annotator B | **Keep / Drop / Edit / Unsure** |

Impact repository rows (OwnerRepository / VetRepository / PetTypeRepository): list **production** inject sites only unless a task explicitly says otherwise.

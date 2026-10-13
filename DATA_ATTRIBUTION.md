# Restaurant resource attribution

This document applies to `resources/CamRestaurants-dbase.db` and
`resources/CamRestaurants-rules.json`. It does not assign a license to the
application source code, tests, or the project as a whole.

## Original dataset: Cambridge CamRest676

The underlying restaurant data and ontology originate from Cambridge
CamRest676, collected by the Cambridge Dialogue Systems Group.
The official University of Cambridge deposit lists Tsung-Hsien Wen,
Nikola Mrkšić, and Steve Young as dataset authors.

- Official deposit: https://www.repository.cam.ac.uk/items/011514c6-ee59-4a44-aa24-baab91001149
- Persistent identifier: https://doi.org/10.17863/CAM.6142
- Original handle: https://www.repository.cam.ac.uk/handle/1810/260970
- Original download: https://api.repository.cam.ac.uk/server/api/core/bitstreams/e15be918-187f-4ef4-be92-3c09f8e08296/content

The deposit declares Creative Commons Attribution 4.0 International
(CC BY 4.0), except where otherwise noted. Its archive includes
`CamRestDB.json`, `CamRestOTGY.json`, the dialogue corpus, and a README.
The original notice states:

> Copyright Cambridge Dialogue Systems Group, 2016

The original README is preserved unchanged as
`licenses/CamRest676-README.json` (despite its filename, the upstream file
contains plain text). The full CC BY 4.0 legal text is preserved in
`licenses/CC-BY-4.0.txt`.

CC BY 4.0 permits sharing and adaptation subject to its terms, including
appropriate credit, a license reference, preservation of applicable
notices, and disclosure of modifications. Do not imply endorsement or
apply additional restrictions to the licensed material.

- License: https://creativecommons.org/licenses/by/4.0/
- Official legal text source: https://raw.githubusercontent.com/creativecommons/creativecommons.org/main/docroot/legalcode/by_4.0.txt

## Closest matching upstream resources: PyDial

The closest matching public versions are distributed by PyDial under
`ontology/ontologies/CamRestaurants-dbase.db` and
`ontology/ontologies/CamRestaurants-rules.json`:

- Repository: https://bitbucket.org/dialoguesystems/pydial/src/master/
- Database: https://bitbucket.org/dialoguesystems/pydial/raw/master/ontology/ontologies/CamRestaurants-dbase.db
- Rules: https://bitbucket.org/dialoguesystems/pydial/raw/master/ontology/ontologies/CamRestaurants-rules.json
- Upstream license notice: https://bitbucket.org/dialoguesystems/pydial/raw/master/LICENSE

PyDial's license notice identifies:

> Copyright 2015 - 2017
> Cambridge University Engineering Department Dialogue Systems Group

PyDial is distributed under Apache License 2.0. Its original license and
copyright notice is preserved unchanged in `licenses/PyDial-LICENSE.txt`;
the full Apache 2.0 license is preserved in `licenses/Apache-2.0.txt`.
Redistribution requires supplying the license, retaining applicable
copyright and attribution notices, identifying modified files, and
preserving relevant upstream NOTICE attributions if provided. No separate
root NOTICE file was available at the inspected PyDial upstream URL.

- Full Apache license source: https://www.apache.org/licenses/LICENSE-2.0.txt

The public PyDial database and Plato's corresponding database are
byte-identical. The local SQLite database has the same schema and 110
records as PyDial; all fields match except restaurant-name capitalization.
This establishes a close content match, not the instructor's precise
acquisition route. The CamRest CC BY 4.0 notice is retained for the
underlying dataset, and the PyDial Apache 2.0 notices are retained for its
resource distribution and adaptations. Neither is presented as a license
for the entire student application.

## Modifications by the student project team

The two resource files are modified versions of the matching upstream
resources. The student project team made these changes:

- `resources/CamRestaurants-dbase.db`: changed restaurant-name
  capitalization. Relative to public PyDial, the remaining fields in all
  110 records are unchanged.
- `resources/CamRestaurants-rules.json`: adapted the ontology to the
  application's `domain`, `slots`, and `slotvalues` structure; retained
  110 restaurant names and 86 cuisine values; retained the same three
  price ranges and five areas; and included the application's supported
  slots, including `signature`.

These student-team modifications are not attributed to the instructor.
The publication copy preserves both project resource files unchanged.

## Academic references

The original dataset README requests citation of:

1. Tsung-Hsien Wen, Milica Gašić, Nikola Mrkšić, Lina M. Rojas-Barahona,
   Pei-Hao Su, Stefan Ultes, David Vandyke, and Steve Young (2016).
   *Conditional Generation and Snapshot Learning in Neural Dialogue Systems*.
   EMNLP, pp. 2153–2162. https://aclanthology.org/D16-1233/
2. Tsung-Hsien Wen, David Vandyke, Nikola Mrkšić, Milica Gašić,
   Lina M. Rojas-Barahona, Pei-Hao Su, Stefan Ultes, and Steve Young (2017).
   *A Network-based End-to-End Trainable Task-oriented Dialogue System*.
   EACL, pp. 438–449. https://aclanthology.org/E17-1042/

PyDial toolkit reference:
Stefan Ultes et al. (2017). *PyDial: A Multi-domain Statistical Dialogue
System Toolkit*. ACL System Demonstrations, pp. 73–78.
https://aclanthology.org/P17-4013/

Paper availability is not itself redistribution permission. The dataset
and toolkit license statements above provide the relevant upstream terms.

Upstream sources and notices were checked on 12 October 2026.

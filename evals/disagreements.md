# LLM disagreements with Claude-drafted gold labels

**Run: Haiku (claude-haiku-5-5), dev split, N=51 posts, 2026-10-30 America/Toronto.**

Audit these disagreements to check whether the labels favor Claude. Counts are disagreeing posts per field/config, pooled across selected splits.

| Field | B | C | D | E | W | F |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| company | 2 | 6 | 4 | 9 | 3 | 6 |
| salary | 0 | 2 | 1 | 2 | 0 | 2 |
| location | 15 | 20 | 21 | 15 | 16 | 17 |
| skills | 27 | 24 | 22 | 25 | 25 | 29 |
| remote | 6 | 8 | 9 | 14 | 7 | 6 |
| seniority | 6 | 13 | 8 | 9 | 7 | 15 |

Only the six scored fields are included. Nullable extracted/abstained outcomes are agreements; skills disagree whenever normalized per-post F1 is below 1; enums use scorer accuracy. Label values are shown as recorded. Model values are the normalized predictions used for scoring; salary min/max are annualized, while the label retains its original period.

## company

### Config B (2)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858476&quot;</code> | <code>&quot;Okta&quot;</code> | <code>&quot;Okta/Auth0&quot;</code> |
| dev | <code>&quot;46859924&quot;</code> | <code>&quot;Mem0&quot;</code> | <code>&quot;Mem0.ai&quot;</code> |

### Config C (6)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858476&quot;</code> | <code>&quot;Okta&quot;</code> | <code>&quot;Okta/Auth0&quot;</code> |
| dev | <code>&quot;46859924&quot;</code> | <code>&quot;Mem0&quot;</code> | <code>&quot;Mem0.ai&quot;</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>&quot;Duckbill&quot;</code> | <code>null</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>&quot;MiLaboratories&quot;</code> | <code>null</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;Neo.Tax&quot;</code> | <code>null</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>&quot;Rabbet&quot;</code> | <code>null</code> |

### Config D (4)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858476&quot;</code> | <code>&quot;Okta&quot;</code> | <code>&quot;Okta/Auth0&quot;</code> |
| dev | <code>&quot;46863917&quot;</code> | <code>&quot;Plutus&quot;</code> | <code>null</code> |
| dev | <code>&quot;47673074&quot;</code> | <code>&quot;Flow Traders&quot;</code> | <code>null</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>&quot;MiLaboratories&quot;</code> | <code>null</code> |

### Config E (9)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858476&quot;</code> | <code>&quot;Okta&quot;</code> | <code>&quot;Okta/Auth0&quot;</code> |
| dev | <code>&quot;46859924&quot;</code> | <code>&quot;Mem0&quot;</code> | <code>&quot;Mem0.ai&quot;</code> |
| dev | <code>&quot;47220091&quot;</code> | <code>&quot;Flux.ai&quot;</code> | <code>null</code> |
| dev | <code>&quot;47220599&quot;</code> | <code>&quot;Sesame&quot;</code> | <code>null</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>&quot;Courted&quot;</code> | <code>null</code> |
| dev | <code>&quot;47256159&quot;</code> | <code>&quot;LiveKit&quot;</code> | <code>null</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>&quot;yeet&quot;</code> | <code>null</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>&quot;UMH&quot;</code> | <code>null</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;Neo.Tax&quot;</code> | <code>null</code> |

### Config W (3)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858476&quot;</code> | <code>&quot;Okta&quot;</code> | <code>&quot;Okta/Auth0&quot;</code> |
| dev | <code>&quot;46859924&quot;</code> | <code>&quot;Mem0&quot;</code> | <code>&quot;Mem0.ai&quot;</code> |
| dev | <code>&quot;47220989&quot;</code> | <code>&quot;Impinj&quot;</code> | <code>null</code> |

### Config F (6)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858476&quot;</code> | <code>&quot;Okta&quot;</code> | <code>&quot;Okta/Auth0&quot;</code> |
| dev | <code>&quot;46859924&quot;</code> | <code>&quot;Mem0&quot;</code> | <code>&quot;Mem0.ai&quot;</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>&quot;Courted&quot;</code> | <code>&quot;Courted (https://courted.io)&quot;</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>&quot;UMH&quot;</code> | <code>&quot;Cologne, Germany&quot;</code> |
| dev | <code>&quot;48358258&quot;</code> | <code>&quot;Twindo&quot;</code> | <code>&quot;Twindo (Formerly Canvas; The Spatial Computing Company)&quot;</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>&quot;Rabbet&quot;</code> | <code>&quot;Rabbet (YC S17)&quot;</code> |

## salary

### Config B (0)

No disagreements.

### Config C (2)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;47976872&quot;</code> | <code>{&quot;min&quot;: 90000, &quot;max&quot;: 120000, &quot;period&quot;: &quot;year&quot;}</code> | <code>{&quot;min&quot;: null, &quot;max&quot;: null}</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>{&quot;min&quot;: 190000, &quot;max&quot;: 210000, &quot;period&quot;: &quot;year&quot;}</code> | <code>{&quot;min&quot;: null, &quot;max&quot;: null}</code> |

### Config D (1)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;47976872&quot;</code> | <code>{&quot;min&quot;: 90000, &quot;max&quot;: 120000, &quot;period&quot;: &quot;year&quot;}</code> | <code>{&quot;min&quot;: null, &quot;max&quot;: null}</code> |

### Config E (2)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;48021354&quot;</code> | <code>{&quot;min&quot;: 55000, &quot;max&quot;: 85000, &quot;period&quot;: &quot;year&quot;}</code> | <code>{&quot;min&quot;: null, &quot;max&quot;: null}</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>{&quot;min&quot;: 190000, &quot;max&quot;: 210000, &quot;period&quot;: &quot;year&quot;}</code> | <code>{&quot;min&quot;: null, &quot;max&quot;: null}</code> |

### Config W (0)

No disagreements.

### Config F (2)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;48021354&quot;</code> | <code>{&quot;min&quot;: 55000, &quot;max&quot;: 85000, &quot;period&quot;: &quot;year&quot;}</code> | <code>{&quot;min&quot;: null, &quot;max&quot;: null}</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>{&quot;min&quot;: 225000, &quot;max&quot;: 270000, &quot;period&quot;: &quot;year&quot;}</code> | <code>{&quot;min&quot;: null, &quot;max&quot;: null}</code> |

## location

### Config B (15)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858532&quot;</code> | <code>&quot;Boston&quot;</code> | <code>&quot;Boston or Remote (US)&quot;</code> |
| dev | <code>&quot;46859629&quot;</code> | <code>&quot;New York&quot;</code> | <code>&quot;NY&quot;</code> |
| dev | <code>&quot;46869120&quot;</code> | <code>&quot;Chicago, IL&quot;</code> | <code>&quot;Chicago, IL (Hybrid Tue/Thu) or Remote (US)&quot;</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>&quot;Europe&quot;</code> | <code>&quot;Europe-friendly time zones&quot;</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;downtown SF&quot;</code> |
| dev | <code>&quot;46893914&quot;</code> | <code>&quot;US&quot;</code> | <code>&quot;US time zone&quot;</code> |
| dev | <code>&quot;47220599&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;SF/NYC/Bellevue&quot;</code> |
| dev | <code>&quot;47610945&quot;</code> | <code>&quot;Netherlands&quot;</code> | <code>&quot;Remote or Netherlands&quot;</code> |
| dev | <code>&quot;47676433&quot;</code> | <code>&quot;North America, Europe&quot;</code> | <code>&quot;Remote (North America &amp; Europe)&quot;</code> |
| dev | <code>&quot;47975959&quot;</code> | <code>&quot;EU&quot;</code> | <code>&quot;EU time zone&quot;</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>null</code> | <code>&quot;Helsinki HQ&quot;</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;US&quot;</code> | <code>&quot;US (Pacific hours)&quot;</code> |
| dev | <code>&quot;48787393&quot;</code> | <code>null</code> | <code>&quot;US overlap preferred&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;Denver, CO&quot;</code> | <code>&quot;Denver, CO, USA&quot;</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>&quot;TX, NC, CO&quot;</code> | <code>&quot;TX, NC, or CO (US states)&quot;</code> |

### Config C (20)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858532&quot;</code> | <code>&quot;Boston&quot;</code> | <code>&quot;Boston or Remote (US)&quot;</code> |
| dev | <code>&quot;46859629&quot;</code> | <code>&quot;New York&quot;</code> | <code>&quot;NY&quot;</code> |
| dev | <code>&quot;46869120&quot;</code> | <code>&quot;Chicago, IL&quot;</code> | <code>&quot;Chicago, IL (hybrid Tue/Thu) or remote (US)&quot;</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>&quot;Europe&quot;</code> | <code>&quot;Remote (Europe-friendly time zones)&quot;</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>null</code> |
| dev | <code>&quot;46893914&quot;</code> | <code>&quot;US&quot;</code> | <code>null</code> |
| dev | <code>&quot;47220599&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;SF/NYC/Bellevue&quot;</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>&quot;US&quot;</code> | <code>&quot;REMOTE (US)&quot;</code> |
| dev | <code>&quot;47610945&quot;</code> | <code>&quot;Netherlands&quot;</code> | <code>&quot;Remote or Netherlands&quot;</code> |
| dev | <code>&quot;47676433&quot;</code> | <code>&quot;North America, Europe&quot;</code> | <code>&quot;North America &amp; Europe&quot;</code> |
| dev | <code>&quot;47975959&quot;</code> | <code>&quot;EU&quot;</code> | <code>null</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>&quot;Bilbao, Spain&quot;</code> | <code>null</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>&quot;Toronto, ON&quot;</code> | <code>&quot;Toronto, ON (Hybrid) + Remote&quot;</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>&quot;Chicago, IL&quot;</code> | <code>&quot;Chicago, IL / Remote&quot;</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>null</code> | <code>&quot;Helsinki&quot;</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;US&quot;</code> | <code>null</code> |
| dev | <code>&quot;48365334&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;San Francisco / Remote&quot;</code> |
| dev | <code>&quot;48787393&quot;</code> | <code>null</code> | <code>&quot;US overlap preferred&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;Denver, CO&quot;</code> | <code>&quot;Denver, CO, USA&quot;</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>&quot;TX, NC, CO&quot;</code> | <code>null</code> |

### Config D (21)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858532&quot;</code> | <code>&quot;Boston&quot;</code> | <code>&quot;Boston or Remote (US)&quot;</code> |
| dev | <code>&quot;46859629&quot;</code> | <code>&quot;New York&quot;</code> | <code>&quot;NY&quot;</code> |
| dev | <code>&quot;46863917&quot;</code> | <code>&quot;Kirkland, WA&quot;</code> | <code>null</code> |
| dev | <code>&quot;46869120&quot;</code> | <code>&quot;Chicago, IL&quot;</code> | <code>&quot;Chicago, IL (Hybrid Tue/Thu) or Remote (US)&quot;</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>&quot;Europe&quot;</code> | <code>&quot;Europe-friendly time zones&quot;</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;downtown SF&quot;</code> |
| dev | <code>&quot;46893914&quot;</code> | <code>&quot;US&quot;</code> | <code>null</code> |
| dev | <code>&quot;47220599&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;SF/NYC/Bellevue&quot;</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>&quot;US&quot;</code> | <code>&quot;REMOTE (US)&quot;</code> |
| dev | <code>&quot;47605460&quot;</code> | <code>&quot;Germany, UK&quot;</code> | <code>&quot;Germany/UK&quot;</code> |
| dev | <code>&quot;47610945&quot;</code> | <code>&quot;Netherlands&quot;</code> | <code>&quot;Remote or Netherlands&quot;</code> |
| dev | <code>&quot;47673074&quot;</code> | <code>&quot;Hong Kong&quot;</code> | <code>null</code> |
| dev | <code>&quot;47676433&quot;</code> | <code>&quot;North America, Europe&quot;</code> | <code>&quot;North America &amp; Europe&quot;</code> |
| dev | <code>&quot;47975959&quot;</code> | <code>&quot;EU&quot;</code> | <code>&quot;Remote (EU time zone) + Quarterly Meet-ups&quot;</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>&quot;Bilbao, Spain&quot;</code> | <code>null</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>&quot;Chicago, IL&quot;</code> | <code>&quot;Chicago, IL / Remote&quot;</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>null</code> | <code>&quot;Helsinki HQ&quot;</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;US&quot;</code> | <code>&quot;US (Pacific hours)&quot;</code> |
| dev | <code>&quot;48787393&quot;</code> | <code>null</code> | <code>&quot;US overlap preferred&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;Denver, CO&quot;</code> | <code>&quot;Denver, CO, USA&quot;</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>&quot;TX, NC, CO&quot;</code> | <code>&quot;TX, NC, or CO (US)&quot;</code> |

### Config E (15)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858532&quot;</code> | <code>&quot;Boston&quot;</code> | <code>&quot;Boston or Remote (US)&quot;</code> |
| dev | <code>&quot;46859629&quot;</code> | <code>&quot;New York&quot;</code> | <code>&quot;NY&quot;</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>&quot;Europe&quot;</code> | <code>&quot;Europe-friendly time zones&quot;</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;downtown SF&quot;</code> |
| dev | <code>&quot;46893914&quot;</code> | <code>&quot;US&quot;</code> | <code>&quot;US time zone&quot;</code> |
| dev | <code>&quot;47220091&quot;</code> | <code>&quot;San Francisco, CA&quot;</code> | <code>null</code> |
| dev | <code>&quot;47220599&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>null</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>&quot;NYC&quot;</code> | <code>null</code> |
| dev | <code>&quot;47676433&quot;</code> | <code>&quot;North America, Europe&quot;</code> | <code>&quot;North America &amp; Europe&quot;</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>&quot;Chicago, IL&quot;</code> | <code>null</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>&quot;Cologne, Germany&quot;</code> | <code>null</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>null</code> | <code>&quot;Helsinki&quot;</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;US&quot;</code> | <code>null</code> |
| dev | <code>&quot;48787393&quot;</code> | <code>null</code> | <code>&quot;US&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;Denver, CO&quot;</code> | <code>&quot;Denver, CO, USA&quot;</code> |

### Config W (16)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858532&quot;</code> | <code>&quot;Boston&quot;</code> | <code>&quot;Boston or Remote (US)&quot;</code> |
| dev | <code>&quot;46859629&quot;</code> | <code>&quot;New York&quot;</code> | <code>&quot;NY&quot;</code> |
| dev | <code>&quot;46869120&quot;</code> | <code>&quot;Chicago, IL&quot;</code> | <code>&quot;Chicago, IL (Hybrid Tue/Thu) or Remote (US)&quot;</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>&quot;Europe&quot;</code> | <code>&quot;Europe-friendly time zones&quot;</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;downtown SF&quot;</code> |
| dev | <code>&quot;46893914&quot;</code> | <code>&quot;US&quot;</code> | <code>&quot;US time zone&quot;</code> |
| dev | <code>&quot;47220599&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;SF/NYC/Bellevue&quot;</code> |
| dev | <code>&quot;47220989&quot;</code> | <code>&quot;Seattle, WA&quot;</code> | <code>null</code> |
| dev | <code>&quot;47605460&quot;</code> | <code>&quot;Germany, UK&quot;</code> | <code>null</code> |
| dev | <code>&quot;47610945&quot;</code> | <code>&quot;Netherlands&quot;</code> | <code>&quot;Remote or Netherlands&quot;</code> |
| dev | <code>&quot;47676433&quot;</code> | <code>&quot;North America, Europe&quot;</code> | <code>&quot;Remote (North America &amp; Europe)&quot;</code> |
| dev | <code>&quot;47975959&quot;</code> | <code>&quot;EU&quot;</code> | <code>&quot;EU time zone&quot;</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>null</code> | <code>&quot;Helsinki HQ&quot;</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;US&quot;</code> | <code>null</code> |
| dev | <code>&quot;48787393&quot;</code> | <code>null</code> | <code>&quot;US overlap preferred&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;Denver, CO&quot;</code> | <code>&quot;Denver, CO, USA&quot;</code> |

### Config F (17)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46859629&quot;</code> | <code>&quot;New York&quot;</code> | <code>&quot;NY-based&quot;</code> |
| dev | <code>&quot;46863917&quot;</code> | <code>&quot;Kirkland, WA&quot;</code> | <code>&quot;Kirkland, WA (In Person)&quot;</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>&quot;Europe&quot;</code> | <code>&quot;EU&quot;</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;downtown SF&quot;</code> |
| dev | <code>&quot;46959004&quot;</code> | <code>null</code> | <code>&quot;Remote&quot;</code> |
| dev | <code>&quot;47220599&quot;</code> | <code>&quot;San Francisco&quot;</code> | <code>&quot;SF, NYC, Bellevue&quot;</code> |
| dev | <code>&quot;47256159&quot;</code> | <code>null</code> | <code>&quot;Remote&quot;</code> |
| dev | <code>&quot;47308369&quot;</code> | <code>null</code> | <code>&quot;Remote&quot;</code> |
| dev | <code>&quot;47610945&quot;</code> | <code>&quot;Netherlands&quot;</code> | <code>&quot;Remote or Netherlands&quot;</code> |
| dev | <code>&quot;47614308&quot;</code> | <code>null</code> | <code>&quot;Remote&quot;</code> |
| dev | <code>&quot;48023051&quot;</code> | <code>&quot;London&quot;</code> | <code>&quot;London office&quot;</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>null</code> | <code>&quot;Remote (Helsinki HQ)&quot;</code> |
| dev | <code>&quot;48358258&quot;</code> | <code>&quot;Latin America&quot;</code> | <code>&quot;Latin America Remote&quot;</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;US&quot;</code> | <code>&quot;US, Pacific&quot;</code> |
| dev | <code>&quot;48787393&quot;</code> | <code>null</code> | <code>&quot;US&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;Denver, CO&quot;</code> | <code>&quot;Varies between&quot;</code> |
| dev | <code>&quot;48804695&quot;</code> | <code>null</code> | <code>&quot;Fully remote&quot;</code> |

## skills

### Config B (27)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858532&quot;</code> | <code>[&quot;Cypress&quot;, &quot;Playwright&quot;]</code> | <code>[&quot;cypress&quot;, &quot;manual testing&quot;, &quot;playwright&quot;, &quot;test automation&quot;, &quot;web app testing&quot;]</code> |
| dev | <code>&quot;46863917&quot;</code> | <code>[&quot;Google Cloud&quot;, &quot;Kubernetes&quot;, &quot;Node.js&quot;, &quot;TypeScript&quot;, &quot;React&quot;, &quot;PostgreSQL&quot;, &quot;Redis&quot;, &quot;Terraform&quot;, &quot;Docker&quot;]</code> | <code>[&quot;cloud armor&quot;, &quot;cloud run&quot;, &quot;cloud sql&quot;, &quot;docker&quot;, &quot;google cloud&quot;, &quot;kubernetes&quot;, &quot;node.js&quot;, &quot;postgresql&quot;, &quot;react&quot;, &quot;redis&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>[&quot;Angular&quot;, &quot;TypeScript&quot;, &quot;NestJS&quot;, &quot;PostgreSQL&quot;, &quot;AWS&quot;, &quot;Docker&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;angular&quot;, &quot;aws&quot;, &quot;ci/cd&quot;, &quot;docker&quot;, &quot;ecs&quot;, &quot;eks&quot;, &quot;lambda&quot;, &quot;nestjs&quot;, &quot;postgresql&quot;, &quot;rds&quot;, &quot;s3&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;46875351&quot;</code> | <code>[&quot;Swift&quot;, &quot;Metal&quot;, &quot;ARKit&quot;, &quot;Core ML&quot;]</code> | <code>[&quot;arkit&quot;, &quot;ci/cd&quot;, &quot;coreml&quot;, &quot;it&quot;, &quot;metal&quot;, &quot;mobile&quot;, &quot;qa&quot;, &quot;software&quot;, &quot;swift&quot;, &quot;tpm&quot;]</code> |
| dev | <code>&quot;46893914&quot;</code> | <code>[&quot;Rust&quot;]</code> | <code>[&quot;back-end&quot;, &quot;distributed architectures&quot;, &quot;financial infrastructure&quot;, &quot;low-latency systems&quot;, &quot;rust&quot;]</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>[&quot;Python&quot;, &quot;Django&quot;, &quot;Django REST Framework&quot;, &quot;PostgreSQL&quot;, &quot;PostGIS&quot;, &quot;Celery&quot;, &quot;Redis&quot;, &quot;AWS&quot;, &quot;SQL&quot;, &quot;OpenAI&quot;, &quot;HubSpot&quot;, &quot;Twilio&quot;]</code> | <code>[&quot;aws&quot;, &quot;celery&quot;, &quot;django&quot;, &quot;django rest framework&quot;, &quot;ecs&quot;, &quot;lambda&quot;, &quot;llm integration&quot;, &quot;postgis&quot;, &quot;postgresql&quot;, &quot;python&quot;, &quot;rds&quot;, &quot;redis&quot;, &quot;s3&quot;, &quot;sql optimization&quot;]</code> |
| dev | <code>&quot;47225525&quot;</code> | <code>[&quot;Node.js&quot;, &quot;Express&quot;, &quot;React&quot;, &quot;MongoDB&quot;]</code> | <code>[&quot;express.js&quot;, &quot;mongodb&quot;, &quot;node.js&quot;, &quot;react&quot;]</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>[&quot;Python&quot;, &quot;R&quot;, &quot;TypeScript&quot;, &quot;C++&quot;, &quot;Django&quot;, &quot;React&quot;, &quot;TensorFlow&quot;, &quot;PyTorch&quot;, &quot;scikit-learn&quot;, &quot;Qt&quot;, &quot;Terraform&quot;, &quot;Claude Code&quot;]</code> | <code>[&quot;c++&quot;, &quot;django&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;qt&quot;, &quot;r&quot;, &quot;react&quot;, &quot;scikit-learn&quot;, &quot;tensorflow&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47255238&quot;</code> | <code>[&quot;Go&quot;, &quot;Rust&quot;, &quot;AWS&quot;]</code> | <code>[&quot;aws&quot;, &quot;device fingerprinting&quot;, &quot;go&quot;, &quot;rust&quot;]</code> |
| dev | <code>&quot;47256159&quot;</code> | <code>[&quot;WebRTC&quot;]</code> | <code>[&quot;billing&quot;, &quot;distributed systems&quot;, &quot;security&quot;, &quot;voice ai&quot;, &quot;webrtc&quot;]</code> |
| dev | <code>&quot;47605460&quot;</code> | <code>[&quot;Svelte&quot;, &quot;SvelteKit&quot;, &quot;TypeScript&quot;, &quot;Tailwind CSS&quot;]</code> | <code>[&quot;java&quot;, &quot;kubernetes&quot;, &quot;python&quot;, &quot;rust&quot;, &quot;svelte&quot;, &quot;sveltekit&quot;, &quot;tailwindcss&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47610945&quot;</code> | <code>[&quot;Node.js&quot;, &quot;Laravel&quot;, &quot;React&quot;, &quot;TypeScript&quot;]</code> | <code>[&quot;ai workflows&quot;, &quot;laravel&quot;, &quot;node.js&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>[&quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[&quot;ai-assisted development&quot;, &quot;asynchronous processing&quot;, &quot;backend systems&quot;, &quot;background processing&quot;, &quot;claude&quot;, &quot;data flow&quot;, &quot;document ingestion&quot;, &quot;document parsing&quot;, &quot;openai codex&quot;, &quot;service boundaries&quot;, &quot;system architecture&quot;]</code> |
| dev | <code>&quot;47673074&quot;</code> | <code>[&quot;Python&quot;, &quot;Ray&quot;, &quot;NumPy&quot;, &quot;PyTorch&quot;, &quot;pandas&quot;]</code> | <code>[&quot;cloud technologies&quot;, &quot;math&quot;, &quot;ml pipelines&quot;, &quot;modern dev practices&quot;, &quot;numpy&quot;, &quot;pandas&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;ray&quot;, &quot;stats&quot;]</code> |
| dev | <code>&quot;47975959&quot;</code> | <code>[]</code> | <code>[&quot;applied category theory&quot;, &quot;bayesian methods&quot;, &quot;interest rate prediction models&quot;, &quot;probabilistic modeling&quot;, &quot;program synthesis&quot;, &quot;quantitative default-probability models&quot;, &quot;quantitative modeling&quot;, &quot;valuation models&quot;]</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Tengo&quot;, &quot;Rust&quot;, &quot;Parquet&quot;, &quot;DataFusion&quot;, &quot;Polars&quot;, &quot;pnpm&quot;, &quot;Turborepo&quot;, &quot;Node.js&quot;]</code> | <code>[&quot;bioinformatics&quot;, &quot;datafusion&quot;, &quot;node.js&quot;, &quot;parquet&quot;, &quot;pnpm&quot;, &quot;polars&quot;, &quot;rust&quot;, &quot;tengo&quot;, &quot;turbo&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>[&quot;Ruby on Rails&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;ai agents&quot;, &quot;apis&quot;, &quot;ci/cd&quot;, &quot;llm&quot;, &quot;ruby&quot;, &quot;ruby on rails&quot;, &quot;slos&quot;, &quot;terraform&quot;]</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>[&quot;Rust&quot;, &quot;Linux&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;dev tools&quot;, &quot;distributed systems&quot;, &quot;highly-concurrent multi-threaded programming&quot;, &quot;linux bpf&quot;, &quot;linux internals&quot;, &quot;rust&quot;, &quot;systems programming&quot;]</code> |
| dev | <code>&quot;47986820&quot;</code> | <code>[]</code> | <code>[&quot;laravel&quot;, &quot;next.js&quot;, &quot;node.js&quot;, &quot;react.js&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>[&quot;Benthos&quot;, &quot;Docker&quot;]</code> | <code>[&quot;benthos&quot;, &quot;docker&quot;, &quot;ui&quot;]</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;React&quot;, &quot;Claude Code&quot;, &quot;Codex&quot;, &quot;MCP&quot;]</code> | <code>[&quot;agentic coding&quot;, &quot;ai in production&quot;, &quot;claude code&quot;, &quot;codex&quot;, &quot;design&quot;, &quot;evals&quot;, &quot;mcp&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48358258&quot;</code> | <code>[&quot;iOS&quot;, &quot;Python&quot;, &quot;Django&quot;]</code> | <code>[&quot;3d&quot;, &quot;cad&quot;, &quot;computer vision&quot;, &quot;django&quot;, &quot;geomatics&quot;, &quot;ios&quot;, &quot;photogrammetry&quot;, &quot;python&quot;, &quot;slam&quot;]</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Node.js&quot;, &quot;React&quot;, &quot;GraphQL&quot;, &quot;Google Cloud&quot;, &quot;AWS&quot;, &quot;Azure&quot;, &quot;Terraform&quot;, &quot;Python&quot;, &quot;NumPy&quot;, &quot;Pandas&quot;, &quot;scikit-learn&quot;, &quot;PyTorch&quot;, &quot;SQL&quot;]</code> | <code>[&quot;aws&quot;, &quot;azure&quot;, &quot;google cloud&quot;, &quot;graphql&quot;, &quot;llms&quot;, &quot;ml&quot;, &quot;node.js&quot;, &quot;numpy&quot;, &quot;pandas&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;rag&quot;, &quot;react&quot;, &quot;sklearn&quot;, &quot;sql&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48365334&quot;</code> | <code>[&quot;Kubernetes&quot;]</code> | <code>[&quot;bare-metal automation&quot;, &quot;datacenter bring-up&quot;, &quot;gpu clusters&quot;, &quot;iac&quot;, &quot;kubernetes-as-a-service&quot;, &quot;networking&quot;, &quot;security&quot;, &quot;sre&quot;, &quot;storage&quot;]</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>[&quot;Go&quot;, &quot;Rust&quot;, &quot;Python&quot;, &quot;C&quot;, &quot;C++&quot;, &quot;Linux&quot;, &quot;Kubernetes&quot;, &quot;AWS&quot;, &quot;Google Cloud&quot;, &quot;Azure&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;aws&quot;, &quot;azure&quot;, &quot;c&quot;, &quot;c++&quot;, &quot;distributed systems&quot;, &quot;ebpf&quot;, &quot;go&quot;, &quot;google cloud&quot;, &quot;kubernetes&quot;, &quot;linux internals&quot;, &quot;networking&quot;, &quot;python&quot;, &quot;rust&quot;]</code> |
| dev | <code>&quot;48804695&quot;</code> | <code>[]</code> | <code>[&quot;ai&quot;, &quot;frontend engineering&quot;]</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>[&quot;Elixir&quot;, &quot;Phoenix&quot;, &quot;Absinthe&quot;, &quot;PostgreSQL&quot;, &quot;Google Cloud&quot;, &quot;React&quot;, &quot;TypeScript&quot;, &quot;JavaScript&quot;, &quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[&quot;absinthe&quot;, &quot;elixir&quot;, &quot;google cloud&quot;, &quot;javascript&quot;, &quot;phoenix&quot;, &quot;postgresql&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |

### Config C (24)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46869120&quot;</code> | <code>[]</code> | <code>[&quot;product management&quot;, &quot;systems thinking&quot;, &quot;technical project management&quot;]</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>[&quot;Angular&quot;, &quot;TypeScript&quot;, &quot;NestJS&quot;, &quot;PostgreSQL&quot;, &quot;AWS&quot;, &quot;Docker&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;angular&quot;, &quot;aws&quot;, &quot;docker&quot;, &quot;postgresql&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;46875351&quot;</code> | <code>[&quot;Swift&quot;, &quot;Metal&quot;, &quot;ARKit&quot;, &quot;Core ML&quot;]</code> | <code>[&quot;arkit&quot;, &quot;ci/cd&quot;, &quot;coreml&quot;, &quot;mdm&quot;, &quot;metal&quot;, &quot;swift&quot;]</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;JavaScript&quot;, &quot;React&quot;, &quot;Python&quot;, &quot;Airflow&quot;, &quot;DuckDB&quot;, &quot;S3&quot;, &quot;BigQuery&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>[&quot;Python&quot;, &quot;Django&quot;, &quot;Django REST Framework&quot;, &quot;PostgreSQL&quot;, &quot;PostGIS&quot;, &quot;Celery&quot;, &quot;Redis&quot;, &quot;AWS&quot;, &quot;SQL&quot;, &quot;OpenAI&quot;, &quot;HubSpot&quot;, &quot;Twilio&quot;]</code> | <code>[&quot;aws&quot;, &quot;celery&quot;, &quot;django&quot;, &quot;django rest framework&quot;, &quot;hubspot&quot;, &quot;openai&quot;, &quot;postgis&quot;, &quot;postgresql&quot;, &quot;python&quot;, &quot;redis&quot;, &quot;twilio&quot;]</code> |
| dev | <code>&quot;47225525&quot;</code> | <code>[&quot;Node.js&quot;, &quot;Express&quot;, &quot;React&quot;, &quot;MongoDB&quot;]</code> | <code>[&quot;express.js&quot;, &quot;mongodb&quot;, &quot;node.js&quot;, &quot;react&quot;]</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>[&quot;Python&quot;, &quot;R&quot;, &quot;TypeScript&quot;, &quot;C++&quot;, &quot;Django&quot;, &quot;React&quot;, &quot;TensorFlow&quot;, &quot;PyTorch&quot;, &quot;scikit-learn&quot;, &quot;Qt&quot;, &quot;Terraform&quot;, &quot;Claude Code&quot;]</code> | <code>[&quot;c++&quot;, &quot;django&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;qt&quot;, &quot;r&quot;, &quot;react&quot;, &quot;scikit-learn&quot;, &quot;tensorflow&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47256159&quot;</code> | <code>[&quot;WebRTC&quot;]</code> | <code>[&quot;voice ai&quot;, &quot;webrtc&quot;]</code> |
| dev | <code>&quot;47605460&quot;</code> | <code>[&quot;Svelte&quot;, &quot;SvelteKit&quot;, &quot;TypeScript&quot;, &quot;Tailwind CSS&quot;]</code> | <code>[&quot;kubernetes&quot;, &quot;rust&quot;, &quot;svelte&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>[&quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[&quot;ai tools&quot;, &quot;asynchronous processing&quot;, &quot;backend&quot;, &quot;background processing&quot;, &quot;data flow&quot;, &quot;document ingestion&quot;, &quot;document parsing&quot;, &quot;maintainability&quot;, &quot;reliability&quot;, &quot;scalability&quot;, &quot;service boundaries&quot;, &quot;system architecture&quot;]</code> |
| dev | <code>&quot;47673074&quot;</code> | <code>[&quot;Python&quot;, &quot;Ray&quot;, &quot;NumPy&quot;, &quot;PyTorch&quot;, &quot;pandas&quot;]</code> | <code>[&quot;python&quot;, &quot;pytorch&quot;]</code> |
| dev | <code>&quot;47975959&quot;</code> | <code>[]</code> | <code>[&quot;bayesian methods&quot;, &quot;category theory&quot;, &quot;default-probability models&quot;, &quot;interest rate prediction models&quot;, &quot;probabilistic modeling&quot;, &quot;program synthesis&quot;, &quot;quantitative modeling&quot;, &quot;valuation models&quot;]</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Tengo&quot;, &quot;Rust&quot;, &quot;Parquet&quot;, &quot;DataFusion&quot;, &quot;Polars&quot;, &quot;pnpm&quot;, &quot;Turborepo&quot;, &quot;Node.js&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>[&quot;Ruby on Rails&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;ai agents&quot;, &quot;apis&quot;, &quot;ci/cd&quot;, &quot;llm&quot;, &quot;ruby on rails&quot;, &quot;slos&quot;, &quot;terraform&quot;]</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>[&quot;Rust&quot;, &quot;Linux&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;rust&quot;]</code> |
| dev | <code>&quot;47986820&quot;</code> | <code>[]</code> | <code>[&quot;laravel&quot;, &quot;next.js&quot;, &quot;node.js&quot;, &quot;react.js&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>[&quot;Benthos&quot;, &quot;Docker&quot;]</code> | <code>[&quot;benthos&quot;, &quot;docker&quot;, &quot;open source&quot;]</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;React&quot;, &quot;Claude Code&quot;, &quot;Codex&quot;, &quot;MCP&quot;]</code> | <code>[&quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48358258&quot;</code> | <code>[&quot;iOS&quot;, &quot;Python&quot;, &quot;Django&quot;]</code> | <code>[&quot;django&quot;, &quot;python&quot;]</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Node.js&quot;, &quot;React&quot;, &quot;GraphQL&quot;, &quot;Google Cloud&quot;, &quot;AWS&quot;, &quot;Azure&quot;, &quot;Terraform&quot;, &quot;Python&quot;, &quot;NumPy&quot;, &quot;Pandas&quot;, &quot;scikit-learn&quot;, &quot;PyTorch&quot;, &quot;SQL&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;48365334&quot;</code> | <code>[&quot;Kubernetes&quot;]</code> | <code>[&quot;bare-metal automation&quot;, &quot;datacenter bring-up&quot;, &quot;gpu clusters&quot;, &quot;iac&quot;, &quot;kubernetes&quot;, &quot;networking&quot;, &quot;security&quot;, &quot;sre&quot;, &quot;storage&quot;]</code> |
| dev | <code>&quot;48376486&quot;</code> | <code>[&quot;PostgreSQL&quot;, &quot;CapRover&quot;, &quot;Docker Swarm&quot;, &quot;Auth0&quot;]</code> | <code>[&quot;auth0&quot;, &quot;docker swarm&quot;, &quot;postgresql&quot;]</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>[&quot;Go&quot;, &quot;Rust&quot;, &quot;Python&quot;, &quot;C&quot;, &quot;C++&quot;, &quot;Linux&quot;, &quot;Kubernetes&quot;, &quot;AWS&quot;, &quot;Google Cloud&quot;, &quot;Azure&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;aws&quot;, &quot;azure&quot;, &quot;c&quot;, &quot;c++&quot;, &quot;distributed systems&quot;, &quot;ebpf&quot;, &quot;go&quot;, &quot;google cloud&quot;, &quot;kubernetes&quot;, &quot;linux&quot;, &quot;networking&quot;, &quot;python&quot;, &quot;rust&quot;]</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>[&quot;Elixir&quot;, &quot;Phoenix&quot;, &quot;Absinthe&quot;, &quot;PostgreSQL&quot;, &quot;Google Cloud&quot;, &quot;React&quot;, &quot;TypeScript&quot;, &quot;JavaScript&quot;, &quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[]</code> |

### Config D (22)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46863917&quot;</code> | <code>[&quot;Google Cloud&quot;, &quot;Kubernetes&quot;, &quot;Node.js&quot;, &quot;TypeScript&quot;, &quot;React&quot;, &quot;PostgreSQL&quot;, &quot;Redis&quot;, &quot;Terraform&quot;, &quot;Docker&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>[&quot;Angular&quot;, &quot;TypeScript&quot;, &quot;NestJS&quot;, &quot;PostgreSQL&quot;, &quot;AWS&quot;, &quot;Docker&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;angular&quot;, &quot;aws&quot;, &quot;docker&quot;, &quot;postgresql&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;46875351&quot;</code> | <code>[&quot;Swift&quot;, &quot;Metal&quot;, &quot;ARKit&quot;, &quot;Core ML&quot;]</code> | <code>[&quot;arkit&quot;, &quot;ci/cd&quot;, &quot;coreml&quot;, &quot;metal&quot;, &quot;swift&quot;]</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>[&quot;Python&quot;, &quot;Django&quot;, &quot;Django REST Framework&quot;, &quot;PostgreSQL&quot;, &quot;PostGIS&quot;, &quot;Celery&quot;, &quot;Redis&quot;, &quot;AWS&quot;, &quot;SQL&quot;, &quot;OpenAI&quot;, &quot;HubSpot&quot;, &quot;Twilio&quot;]</code> | <code>[&quot;aws&quot;, &quot;celery&quot;, &quot;django&quot;, &quot;django rest framework&quot;, &quot;llm integration&quot;, &quot;postgis&quot;, &quot;postgresql&quot;, &quot;python&quot;, &quot;redis&quot;, &quot;sql&quot;]</code> |
| dev | <code>&quot;47225525&quot;</code> | <code>[&quot;Node.js&quot;, &quot;Express&quot;, &quot;React&quot;, &quot;MongoDB&quot;]</code> | <code>[&quot;mongodb&quot;, &quot;node.js&quot;, &quot;react&quot;]</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>[&quot;Python&quot;, &quot;R&quot;, &quot;TypeScript&quot;, &quot;C++&quot;, &quot;Django&quot;, &quot;React&quot;, &quot;TensorFlow&quot;, &quot;PyTorch&quot;, &quot;scikit-learn&quot;, &quot;Qt&quot;, &quot;Terraform&quot;, &quot;Claude Code&quot;]</code> | <code>[&quot;c++&quot;, &quot;django&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;react&quot;, &quot;tensorflow&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47605460&quot;</code> | <code>[&quot;Svelte&quot;, &quot;SvelteKit&quot;, &quot;TypeScript&quot;, &quot;Tailwind CSS&quot;]</code> | <code>[&quot;java&quot;, &quot;kubernetes&quot;, &quot;python&quot;, &quot;rust&quot;, &quot;svelte&quot;, &quot;sveltekit&quot;, &quot;tailwindcss&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>[&quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[&quot;ai tools&quot;, &quot;backend&quot;, &quot;data flow&quot;, &quot;distributed systems&quot;, &quot;system architecture&quot;]</code> |
| dev | <code>&quot;47673074&quot;</code> | <code>[&quot;Python&quot;, &quot;Ray&quot;, &quot;NumPy&quot;, &quot;PyTorch&quot;, &quot;pandas&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47975959&quot;</code> | <code>[]</code> | <code>[&quot;interest rate prediction models&quot;, &quot;quantitative default-probability models&quot;, &quot;valuation models&quot;]</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Tengo&quot;, &quot;Rust&quot;, &quot;Parquet&quot;, &quot;DataFusion&quot;, &quot;Polars&quot;, &quot;pnpm&quot;, &quot;Turborepo&quot;, &quot;Node.js&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>[&quot;Ruby on Rails&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;ai agents&quot;, &quot;apis&quot;, &quot;ci/cd&quot;, &quot;llm engineering&quot;, &quot;ruby on rails&quot;, &quot;slos&quot;, &quot;terraform&quot;]</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>[&quot;Rust&quot;, &quot;Linux&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;rust&quot;]</code> |
| dev | <code>&quot;47986820&quot;</code> | <code>[]</code> | <code>[&quot;laravel&quot;, &quot;next.js&quot;, &quot;node.js&quot;, &quot;react.js&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>[&quot;Benthos&quot;, &quot;Docker&quot;]</code> | <code>[&quot;docker&quot;]</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;React&quot;, &quot;Claude Code&quot;, &quot;Codex&quot;, &quot;MCP&quot;]</code> | <code>[&quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48358258&quot;</code> | <code>[&quot;iOS&quot;, &quot;Python&quot;, &quot;Django&quot;]</code> | <code>[&quot;3d&quot;, &quot;cad&quot;, &quot;computer vision&quot;, &quot;django&quot;, &quot;geomatics&quot;, &quot;ios&quot;, &quot;photogrammetry&quot;, &quot;python&quot;, &quot;slam&quot;]</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Node.js&quot;, &quot;React&quot;, &quot;GraphQL&quot;, &quot;Google Cloud&quot;, &quot;AWS&quot;, &quot;Azure&quot;, &quot;Terraform&quot;, &quot;Python&quot;, &quot;NumPy&quot;, &quot;Pandas&quot;, &quot;scikit-learn&quot;, &quot;PyTorch&quot;, &quot;SQL&quot;]</code> | <code>[&quot;graphql&quot;, &quot;node.js&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;react&quot;, &quot;sql&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48365334&quot;</code> | <code>[&quot;Kubernetes&quot;]</code> | <code>[&quot;bare-metal automation&quot;, &quot;datacenter bring-up&quot;, &quot;gpu clusters&quot;, &quot;iac&quot;, &quot;kubernetes&quot;, &quot;networking&quot;, &quot;security&quot;, &quot;sre&quot;, &quot;storage&quot;]</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>[&quot;Go&quot;, &quot;Rust&quot;, &quot;Python&quot;, &quot;C&quot;, &quot;C++&quot;, &quot;Linux&quot;, &quot;Kubernetes&quot;, &quot;AWS&quot;, &quot;Google Cloud&quot;, &quot;Azure&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;aws&quot;, &quot;azure&quot;, &quot;c&quot;, &quot;c++&quot;, &quot;distributed systems&quot;, &quot;go&quot;, &quot;google cloud&quot;, &quot;kubernetes&quot;, &quot;linux&quot;, &quot;networking&quot;, &quot;python&quot;, &quot;rust&quot;]</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>[&quot;Java&quot;, &quot;PostgreSQL&quot;, &quot;Docker&quot;, &quot;Kubernetes&quot;, &quot;MySQL&quot;, &quot;OAuth&quot;, &quot;SAML&quot;, &quot;OIDC&quot;]</code> | <code>[&quot;docker&quot;, &quot;java&quot;, &quot;kubernetes&quot;, &quot;mysql&quot;, &quot;postgresql&quot;]</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>[&quot;Elixir&quot;, &quot;Phoenix&quot;, &quot;Absinthe&quot;, &quot;PostgreSQL&quot;, &quot;Google Cloud&quot;, &quot;React&quot;, &quot;TypeScript&quot;, &quot;JavaScript&quot;, &quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[&quot;absinthe&quot;, &quot;elixir&quot;, &quot;google cloud&quot;, &quot;phoenix&quot;, &quot;postgresql&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |

### Config E (25)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46863917&quot;</code> | <code>[&quot;Google Cloud&quot;, &quot;Kubernetes&quot;, &quot;Node.js&quot;, &quot;TypeScript&quot;, &quot;React&quot;, &quot;PostgreSQL&quot;, &quot;Redis&quot;, &quot;Terraform&quot;, &quot;Docker&quot;]</code> | <code>[&quot;cloud armor&quot;, &quot;cloud run&quot;, &quot;cloud sql&quot;, &quot;docker&quot;, &quot;google cloud&quot;, &quot;kubernetes&quot;, &quot;node.js&quot;, &quot;postgresql&quot;, &quot;react&quot;, &quot;redis&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>[&quot;Angular&quot;, &quot;TypeScript&quot;, &quot;NestJS&quot;, &quot;PostgreSQL&quot;, &quot;AWS&quot;, &quot;Docker&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;angular&quot;, &quot;aws&quot;, &quot;docker&quot;, &quot;postgresql&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;46875351&quot;</code> | <code>[&quot;Swift&quot;, &quot;Metal&quot;, &quot;ARKit&quot;, &quot;Core ML&quot;]</code> | <code>[&quot;swift&quot;]</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;JavaScript&quot;, &quot;React&quot;, &quot;Python&quot;, &quot;Airflow&quot;, &quot;DuckDB&quot;, &quot;S3&quot;, &quot;BigQuery&quot;]</code> | <code>[&quot;airflow&quot;, &quot;javascript&quot;, &quot;python&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47220091&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;React&quot;, &quot;Node.js&quot;, &quot;Rust&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>[&quot;Python&quot;, &quot;Django&quot;, &quot;Django REST Framework&quot;, &quot;PostgreSQL&quot;, &quot;PostGIS&quot;, &quot;Celery&quot;, &quot;Redis&quot;, &quot;AWS&quot;, &quot;SQL&quot;, &quot;OpenAI&quot;, &quot;HubSpot&quot;, &quot;Twilio&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47225525&quot;</code> | <code>[&quot;Node.js&quot;, &quot;Express&quot;, &quot;React&quot;, &quot;MongoDB&quot;]</code> | <code>[&quot;express.js&quot;, &quot;mongodb&quot;, &quot;node.js&quot;, &quot;react&quot;]</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>[&quot;Python&quot;, &quot;R&quot;, &quot;TypeScript&quot;, &quot;C++&quot;, &quot;Django&quot;, &quot;React&quot;, &quot;TensorFlow&quot;, &quot;PyTorch&quot;, &quot;scikit-learn&quot;, &quot;Qt&quot;, &quot;Terraform&quot;, &quot;Claude Code&quot;]</code> | <code>[&quot;c++&quot;, &quot;django&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;qt&quot;, &quot;r&quot;, &quot;react&quot;, &quot;scikit-learn&quot;, &quot;tensorflow&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47256159&quot;</code> | <code>[&quot;WebRTC&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47603990&quot;</code> | <code>[&quot;Kubernetes&quot;, &quot;AWS&quot;, &quot;Helm&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;aws&quot;, &quot;kubernetes&quot;, &quot;terraform&quot;]</code> |
| dev | <code>&quot;47605460&quot;</code> | <code>[&quot;Svelte&quot;, &quot;SvelteKit&quot;, &quot;TypeScript&quot;, &quot;Tailwind CSS&quot;]</code> | <code>[&quot;airflow&quot;, &quot;java&quot;, &quot;kafka&quot;, &quot;kubernetes&quot;, &quot;python&quot;, &quot;rust&quot;, &quot;svelte&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47610945&quot;</code> | <code>[&quot;Node.js&quot;, &quot;Laravel&quot;, &quot;React&quot;, &quot;TypeScript&quot;]</code> | <code>[&quot;node.js&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>[&quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Tengo&quot;, &quot;Rust&quot;, &quot;Parquet&quot;, &quot;DataFusion&quot;, &quot;Polars&quot;, &quot;pnpm&quot;, &quot;Turborepo&quot;, &quot;Node.js&quot;]</code> | <code>[&quot;polars&quot;, &quot;rust&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>[&quot;Ruby on Rails&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;apis&quot;, &quot;ci/cd&quot;, &quot;llm&quot;, &quot;ruby on rails&quot;, &quot;slos&quot;, &quot;terraform&quot;]</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>[&quot;Rust&quot;, &quot;Linux&quot;, &quot;eBPF&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47986820&quot;</code> | <code>[]</code> | <code>[&quot;next.js&quot;, &quot;node.js&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>[&quot;Benthos&quot;, &quot;Docker&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;React&quot;, &quot;Claude Code&quot;, &quot;Codex&quot;, &quot;MCP&quot;]</code> | <code>[&quot;ai&quot;, &quot;claude code&quot;, &quot;codex&quot;, &quot;mcp&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48358258&quot;</code> | <code>[&quot;iOS&quot;, &quot;Python&quot;, &quot;Django&quot;]</code> | <code>[&quot;django&quot;, &quot;python&quot;]</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Node.js&quot;, &quot;React&quot;, &quot;GraphQL&quot;, &quot;Google Cloud&quot;, &quot;AWS&quot;, &quot;Azure&quot;, &quot;Terraform&quot;, &quot;Python&quot;, &quot;NumPy&quot;, &quot;Pandas&quot;, &quot;scikit-learn&quot;, &quot;PyTorch&quot;, &quot;SQL&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;48376486&quot;</code> | <code>[&quot;PostgreSQL&quot;, &quot;CapRover&quot;, &quot;Docker Swarm&quot;, &quot;Auth0&quot;]</code> | <code>[&quot;postgresql&quot;]</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>[&quot;Go&quot;, &quot;Rust&quot;, &quot;Python&quot;, &quot;C&quot;, &quot;C++&quot;, &quot;Linux&quot;, &quot;Kubernetes&quot;, &quot;AWS&quot;, &quot;Google Cloud&quot;, &quot;Azure&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;aws&quot;, &quot;azure&quot;, &quot;go&quot;, &quot;google cloud&quot;, &quot;kubernetes&quot;, &quot;python&quot;, &quot;rust&quot;]</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>[&quot;Java&quot;, &quot;PostgreSQL&quot;, &quot;Docker&quot;, &quot;Kubernetes&quot;, &quot;MySQL&quot;, &quot;OAuth&quot;, &quot;SAML&quot;, &quot;OIDC&quot;]</code> | <code>[&quot;docker&quot;, &quot;java&quot;, &quot;kubernetes&quot;, &quot;mysql&quot;, &quot;postgresql&quot;]</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>[&quot;Elixir&quot;, &quot;Phoenix&quot;, &quot;Absinthe&quot;, &quot;PostgreSQL&quot;, &quot;Google Cloud&quot;, &quot;React&quot;, &quot;TypeScript&quot;, &quot;JavaScript&quot;, &quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[&quot;absinthe&quot;, &quot;elixir&quot;, &quot;google cloud&quot;, &quot;phoenix&quot;, &quot;postgresql&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |

### Config W (25)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858532&quot;</code> | <code>[&quot;Cypress&quot;, &quot;Playwright&quot;]</code> | <code>[&quot;automated testing&quot;, &quot;cypress&quot;, &quot;manual testing&quot;, &quot;playwright&quot;, &quot;web app testing&quot;]</code> |
| dev | <code>&quot;46863917&quot;</code> | <code>[&quot;Google Cloud&quot;, &quot;Kubernetes&quot;, &quot;Node.js&quot;, &quot;TypeScript&quot;, &quot;React&quot;, &quot;PostgreSQL&quot;, &quot;Redis&quot;, &quot;Terraform&quot;, &quot;Docker&quot;]</code> | <code>[&quot;cloud armor&quot;, &quot;cloud run&quot;, &quot;cloud sql&quot;, &quot;docker&quot;, &quot;google cloud&quot;, &quot;kubernetes&quot;, &quot;node.js&quot;, &quot;postgresql&quot;, &quot;react&quot;, &quot;redis&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>[&quot;Angular&quot;, &quot;TypeScript&quot;, &quot;NestJS&quot;, &quot;PostgreSQL&quot;, &quot;AWS&quot;, &quot;Docker&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;angular&quot;, &quot;aws&quot;, &quot;ci/cd&quot;, &quot;docker&quot;, &quot;ecs&quot;, &quot;eks&quot;, &quot;lambda&quot;, &quot;nestjs&quot;, &quot;postgresql&quot;, &quot;rds&quot;, &quot;s3&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;46875351&quot;</code> | <code>[&quot;Swift&quot;, &quot;Metal&quot;, &quot;ARKit&quot;, &quot;Core ML&quot;]</code> | <code>[&quot;arkit&quot;, &quot;ci/cd&quot;, &quot;cloud identity&quot;, &quot;coreml&quot;, &quot;mdm&quot;, &quot;metal&quot;, &quot;roadmap management&quot;, &quot;sprint operations&quot;, &quot;swift&quot;]</code> |
| dev | <code>&quot;46893914&quot;</code> | <code>[&quot;Rust&quot;]</code> | <code>[&quot;back-end&quot;, &quot;distributed architectures&quot;, &quot;financial infrastructure&quot;, &quot;low-latency systems&quot;, &quot;rust&quot;]</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>[&quot;Python&quot;, &quot;Django&quot;, &quot;Django REST Framework&quot;, &quot;PostgreSQL&quot;, &quot;PostGIS&quot;, &quot;Celery&quot;, &quot;Redis&quot;, &quot;AWS&quot;, &quot;SQL&quot;, &quot;OpenAI&quot;, &quot;HubSpot&quot;, &quot;Twilio&quot;]</code> | <code>[&quot;aws&quot;, &quot;celery&quot;, &quot;django&quot;, &quot;django rest framework&quot;, &quot;ecs&quot;, &quot;hubspot&quot;, &quot;lambda&quot;, &quot;openai&quot;, &quot;postgis&quot;, &quot;postgresql&quot;, &quot;python&quot;, &quot;rds&quot;, &quot;redis&quot;, &quot;s3&quot;, &quot;sql&quot;, &quot;twilio&quot;]</code> |
| dev | <code>&quot;47225525&quot;</code> | <code>[&quot;Node.js&quot;, &quot;Express&quot;, &quot;React&quot;, &quot;MongoDB&quot;]</code> | <code>[&quot;express.js&quot;, &quot;mongodb&quot;, &quot;node.js&quot;, &quot;react&quot;]</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>[&quot;Python&quot;, &quot;R&quot;, &quot;TypeScript&quot;, &quot;C++&quot;, &quot;Django&quot;, &quot;React&quot;, &quot;TensorFlow&quot;, &quot;PyTorch&quot;, &quot;scikit-learn&quot;, &quot;Qt&quot;, &quot;Terraform&quot;, &quot;Claude Code&quot;]</code> | <code>[&quot;c++&quot;, &quot;django&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;qt&quot;, &quot;r&quot;, &quot;react&quot;, &quot;scikit-learn&quot;, &quot;tensorflow&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47256159&quot;</code> | <code>[&quot;WebRTC&quot;]</code> | <code>[&quot;voice ai&quot;, &quot;webrtc&quot;]</code> |
| dev | <code>&quot;47605460&quot;</code> | <code>[&quot;Svelte&quot;, &quot;SvelteKit&quot;, &quot;TypeScript&quot;, &quot;Tailwind CSS&quot;]</code> | <code>[&quot;java&quot;, &quot;kubernetes&quot;, &quot;python&quot;, &quot;rust&quot;, &quot;svelte&quot;, &quot;sveltekit&quot;, &quot;tailwindcss&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47610945&quot;</code> | <code>[&quot;Node.js&quot;, &quot;Laravel&quot;, &quot;React&quot;, &quot;TypeScript&quot;]</code> | <code>[&quot;ai workflows&quot;, &quot;laravel&quot;, &quot;node.js&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>[&quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[&quot;ai-assisted development&quot;, &quot;asynchronous processing&quot;, &quot;backend systems&quot;, &quot;claude&quot;, &quot;data flow&quot;, &quot;document ingestion and parsing&quot;, &quot;openai codex&quot;, &quot;service boundaries&quot;, &quot;system architecture&quot;]</code> |
| dev | <code>&quot;47673074&quot;</code> | <code>[&quot;Python&quot;, &quot;Ray&quot;, &quot;NumPy&quot;, &quot;PyTorch&quot;, &quot;pandas&quot;]</code> | <code>[&quot;cloud technologies&quot;, &quot;ml pipelines&quot;, &quot;numpy&quot;, &quot;pandas&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;ray&quot;]</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Tengo&quot;, &quot;Rust&quot;, &quot;Parquet&quot;, &quot;DataFusion&quot;, &quot;Polars&quot;, &quot;pnpm&quot;, &quot;Turborepo&quot;, &quot;Node.js&quot;]</code> | <code>[&quot;datafusion&quot;, &quot;lua&quot;, &quot;node.js&quot;, &quot;pandas&quot;, &quot;parquet&quot;, &quot;pframes&quot;, &quot;pnpm&quot;, &quot;polars&quot;, &quot;rust&quot;, &quot;tengo&quot;, &quot;turbo&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>[&quot;Ruby on Rails&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;ai agents&quot;, &quot;apis&quot;, &quot;automation&quot;, &quot;capacity planning&quot;, &quot;ci/cd&quot;, &quot;incident management&quot;, &quot;llm&quot;, &quot;ruby&quot;, &quot;ruby on rails&quot;, &quot;slos&quot;, &quot;terraform&quot;]</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>[&quot;Rust&quot;, &quot;Linux&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;dev tools&quot;, &quot;distributed systems&quot;, &quot;linux bpf&quot;, &quot;linux internals&quot;, &quot;multi-threaded programming&quot;, &quot;rust&quot;, &quot;systems programming&quot;]</code> |
| dev | <code>&quot;47986820&quot;</code> | <code>[]</code> | <code>[&quot;laravel&quot;, &quot;next.js&quot;, &quot;node.js&quot;, &quot;react.js&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>[&quot;Benthos&quot;, &quot;Docker&quot;]</code> | <code>[&quot;benthos&quot;, &quot;docker&quot;, &quot;ui design&quot;]</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;React&quot;, &quot;Claude Code&quot;, &quot;Codex&quot;, &quot;MCP&quot;]</code> | <code>[&quot;agents&quot;, &quot;ai in production&quot;, &quot;claude code&quot;, &quot;codex&quot;, &quot;evals&quot;, &quot;mcp&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48358258&quot;</code> | <code>[&quot;iOS&quot;, &quot;Python&quot;, &quot;Django&quot;]</code> | <code>[&quot;3d&quot;, &quot;cad&quot;, &quot;computer vision&quot;, &quot;django&quot;, &quot;geomatics&quot;, &quot;ios&quot;, &quot;photogrammetry&quot;, &quot;python&quot;, &quot;slam&quot;]</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Node.js&quot;, &quot;React&quot;, &quot;GraphQL&quot;, &quot;Google Cloud&quot;, &quot;AWS&quot;, &quot;Azure&quot;, &quot;Terraform&quot;, &quot;Python&quot;, &quot;NumPy&quot;, &quot;Pandas&quot;, &quot;scikit-learn&quot;, &quot;PyTorch&quot;, &quot;SQL&quot;]</code> | <code>[&quot;aws&quot;, &quot;azure&quot;, &quot;google cloud&quot;, &quot;graphql&quot;, &quot;llm fine-tuning&quot;, &quot;node.js&quot;, &quot;numpy&quot;, &quot;pandas&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;rag&quot;, &quot;react&quot;, &quot;sklearn&quot;, &quot;sql&quot;, &quot;synthetic data&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48365334&quot;</code> | <code>[&quot;Kubernetes&quot;]</code> | <code>[&quot;bare-metal automation&quot;, &quot;datacenter bring-up&quot;, &quot;gpu clusters&quot;, &quot;iac&quot;, &quot;kubernetes-as-a-service&quot;, &quot;networking&quot;, &quot;security&quot;, &quot;sre&quot;, &quot;storage&quot;]</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>[&quot;Go&quot;, &quot;Rust&quot;, &quot;Python&quot;, &quot;C&quot;, &quot;C++&quot;, &quot;Linux&quot;, &quot;Kubernetes&quot;, &quot;AWS&quot;, &quot;Google Cloud&quot;, &quot;Azure&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;aws&quot;, &quot;azure&quot;, &quot;c&quot;, &quot;c++&quot;, &quot;distributed systems&quot;, &quot;ebpf&quot;, &quot;go&quot;, &quot;google cloud&quot;, &quot;kubernetes&quot;, &quot;linux&quot;, &quot;networking&quot;, &quot;python&quot;, &quot;rust&quot;]</code> |
| dev | <code>&quot;48804695&quot;</code> | <code>[]</code> | <code>[&quot;ai&quot;, &quot;frontend engineering&quot;]</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>[&quot;Elixir&quot;, &quot;Phoenix&quot;, &quot;Absinthe&quot;, &quot;PostgreSQL&quot;, &quot;Google Cloud&quot;, &quot;React&quot;, &quot;TypeScript&quot;, &quot;JavaScript&quot;, &quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[&quot;absinthe&quot;, &quot;elixir&quot;, &quot;google cloud&quot;, &quot;javascript&quot;, &quot;phoenix&quot;, &quot;postgresql&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |

### Config F (29)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858532&quot;</code> | <code>[&quot;Cypress&quot;, &quot;Playwright&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>[&quot;Angular&quot;, &quot;TypeScript&quot;, &quot;NestJS&quot;, &quot;PostgreSQL&quot;, &quot;AWS&quot;, &quot;Docker&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;angular&quot;, &quot;aws&quot;, &quot;docker&quot;, &quot;postgresql&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;46875351&quot;</code> | <code>[&quot;Swift&quot;, &quot;Metal&quot;, &quot;ARKit&quot;, &quot;Core ML&quot;]</code> | <code>[&quot;swift&quot;]</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;JavaScript&quot;, &quot;React&quot;, &quot;Python&quot;, &quot;Airflow&quot;, &quot;DuckDB&quot;, &quot;S3&quot;, &quot;BigQuery&quot;]</code> | <code>[&quot;airflow&quot;, &quot;python&quot;, &quot;react&quot;]</code> |
| dev | <code>&quot;47220091&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;React&quot;, &quot;Node.js&quot;, &quot;Rust&quot;]</code> | <code>[&quot;llm&quot;, &quot;node.js&quot;, &quot;react&quot;, &quot;rust&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>[&quot;Python&quot;, &quot;Django&quot;, &quot;Django REST Framework&quot;, &quot;PostgreSQL&quot;, &quot;PostGIS&quot;, &quot;Celery&quot;, &quot;Redis&quot;, &quot;AWS&quot;, &quot;SQL&quot;, &quot;OpenAI&quot;, &quot;HubSpot&quot;, &quot;Twilio&quot;]</code> | <code>[&quot;aws&quot;, &quot;django&quot;, &quot;llm&quot;, &quot;postgresql&quot;, &quot;python&quot;, &quot;redis&quot;]</code> |
| dev | <code>&quot;47225525&quot;</code> | <code>[&quot;Node.js&quot;, &quot;Express&quot;, &quot;React&quot;, &quot;MongoDB&quot;]</code> | <code>[&quot;mongodb&quot;, &quot;node.js&quot;, &quot;react&quot;]</code> |
| dev | <code>&quot;47229954&quot;</code> | <code>[&quot;Next.js&quot;, &quot;TypeScript&quot;, &quot;Node.js&quot;, &quot;MongoDB&quot;, &quot;Redis&quot;]</code> | <code>[&quot;go&quot;, &quot;mongodb&quot;, &quot;node.js&quot;, &quot;redis&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>[&quot;Python&quot;, &quot;R&quot;, &quot;TypeScript&quot;, &quot;C++&quot;, &quot;Django&quot;, &quot;React&quot;, &quot;TensorFlow&quot;, &quot;PyTorch&quot;, &quot;scikit-learn&quot;, &quot;Qt&quot;, &quot;Terraform&quot;, &quot;Claude Code&quot;]</code> | <code>[&quot;c++&quot;, &quot;django&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;react&quot;, &quot;tensorflow&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47256159&quot;</code> | <code>[&quot;WebRTC&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47603990&quot;</code> | <code>[&quot;Kubernetes&quot;, &quot;AWS&quot;, &quot;Helm&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;aws&quot;, &quot;kubernetes&quot;, &quot;terraform&quot;]</code> |
| dev | <code>&quot;47605460&quot;</code> | <code>[&quot;Svelte&quot;, &quot;SvelteKit&quot;, &quot;TypeScript&quot;, &quot;Tailwind CSS&quot;]</code> | <code>[&quot;airflow&quot;, &quot;java&quot;, &quot;kafka&quot;, &quot;kubernetes&quot;, &quot;python&quot;, &quot;rust&quot;, &quot;svelte&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47610945&quot;</code> | <code>[&quot;Node.js&quot;, &quot;Laravel&quot;, &quot;React&quot;, &quot;TypeScript&quot;]</code> | <code>[&quot;node.js&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>[&quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;47673074&quot;</code> | <code>[&quot;Python&quot;, &quot;Ray&quot;, &quot;NumPy&quot;, &quot;PyTorch&quot;, &quot;pandas&quot;]</code> | <code>[&quot;python&quot;, &quot;pytorch&quot;]</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Tengo&quot;, &quot;Rust&quot;, &quot;Parquet&quot;, &quot;DataFusion&quot;, &quot;Polars&quot;, &quot;pnpm&quot;, &quot;Turborepo&quot;, &quot;Node.js&quot;]</code> | <code>[&quot;rust&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>[&quot;Ruby on Rails&quot;, &quot;Terraform&quot;]</code> | <code>[&quot;llm&quot;, &quot;ruby&quot;, &quot;ruby on rails&quot;, &quot;terraform&quot;]</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>[&quot;Rust&quot;, &quot;Linux&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;rust&quot;]</code> |
| dev | <code>&quot;47986820&quot;</code> | <code>[]</code> | <code>[&quot;next.js&quot;, &quot;node.js&quot;, &quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>[&quot;Benthos&quot;, &quot;Docker&quot;]</code> | <code>[&quot;docker&quot;]</code> |
| dev | <code>&quot;48102189&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;React&quot;, &quot;Claude Code&quot;, &quot;Codex&quot;, &quot;MCP&quot;]</code> | <code>[&quot;react&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48358258&quot;</code> | <code>[&quot;iOS&quot;, &quot;Python&quot;, &quot;Django&quot;]</code> | <code>[&quot;django&quot;, &quot;python&quot;]</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>[&quot;TypeScript&quot;, &quot;Node.js&quot;, &quot;React&quot;, &quot;GraphQL&quot;, &quot;Google Cloud&quot;, &quot;AWS&quot;, &quot;Azure&quot;, &quot;Terraform&quot;, &quot;Python&quot;, &quot;NumPy&quot;, &quot;Pandas&quot;, &quot;scikit-learn&quot;, &quot;PyTorch&quot;, &quot;SQL&quot;]</code> | <code>[&quot;aws&quot;, &quot;azure&quot;, &quot;google cloud&quot;, &quot;graphql&quot;, &quot;llm&quot;, &quot;python&quot;, &quot;pytorch&quot;, &quot;rag&quot;, &quot;react&quot;, &quot;terraform&quot;, &quot;typescript&quot;]</code> |
| dev | <code>&quot;48376486&quot;</code> | <code>[&quot;PostgreSQL&quot;, &quot;CapRover&quot;, &quot;Docker Swarm&quot;, &quot;Auth0&quot;]</code> | <code>[&quot;docker&quot;, &quot;postgresql&quot;]</code> |
| dev | <code>&quot;48749084&quot;</code> | <code>[]</code> | <code>[&quot;go&quot;, &quot;snowflake&quot;]</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>[&quot;Go&quot;, &quot;Rust&quot;, &quot;Python&quot;, &quot;C&quot;, &quot;C++&quot;, &quot;Linux&quot;, &quot;Kubernetes&quot;, &quot;AWS&quot;, &quot;Google Cloud&quot;, &quot;Azure&quot;, &quot;eBPF&quot;]</code> | <code>[&quot;aws&quot;, &quot;azure&quot;, &quot;c++&quot;, &quot;go&quot;, &quot;google cloud&quot;, &quot;kubernetes&quot;, &quot;mongodb&quot;, &quot;python&quot;, &quot;rust&quot;]</code> |
| dev | <code>&quot;48787393&quot;</code> | <code>[&quot;Flutter&quot;, &quot;Dart&quot;, &quot;Firebase&quot;, &quot;Jaspr&quot;]</code> | <code>[]</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>[&quot;Java&quot;, &quot;PostgreSQL&quot;, &quot;Docker&quot;, &quot;Kubernetes&quot;, &quot;MySQL&quot;, &quot;OAuth&quot;, &quot;SAML&quot;, &quot;OIDC&quot;]</code> | <code>[&quot;docker&quot;, &quot;java&quot;, &quot;kubernetes&quot;, &quot;mysql&quot;, &quot;postgresql&quot;]</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>[&quot;Elixir&quot;, &quot;Phoenix&quot;, &quot;Absinthe&quot;, &quot;PostgreSQL&quot;, &quot;Google Cloud&quot;, &quot;React&quot;, &quot;TypeScript&quot;, &quot;JavaScript&quot;, &quot;Claude&quot;, &quot;Codex&quot;]</code> | <code>[&quot;google cloud&quot;, &quot;postgresql&quot;, &quot;react&quot;]</code> |

## remote

### Config B (6)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46869120&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>&quot;remote&quot;</code> | <code>null</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>&quot;hybrid&quot;</code> | <code>&quot;onsite&quot;</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |

### Config C (8)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46869120&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>&quot;hybrid&quot;</code> | <code>null</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>&quot;remote&quot;</code> | <code>null</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>&quot;onsite&quot;</code> | <code>null</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;remote&quot;</code> | <code>null</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>&quot;remote&quot;</code> | <code>null</code> |

### Config D (9)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46863917&quot;</code> | <code>&quot;onsite&quot;</code> | <code>null</code> |
| dev | <code>&quot;46869120&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>&quot;remote&quot;</code> | <code>null</code> |
| dev | <code>&quot;47673074&quot;</code> | <code>&quot;onsite&quot;</code> | <code>null</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>&quot;onsite&quot;</code> | <code>null</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>&quot;hybrid&quot;</code> | <code>&quot;onsite&quot;</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |

### Config E (14)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46858532&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;46869120&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;47220091&quot;</code> | <code>&quot;onsite&quot;</code> | <code>null</code> |
| dev | <code>&quot;47220599&quot;</code> | <code>&quot;onsite&quot;</code> | <code>null</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>&quot;hybrid&quot;</code> | <code>null</code> |
| dev | <code>&quot;47256159&quot;</code> | <code>&quot;remote&quot;</code> | <code>null</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>&quot;remote&quot;</code> | <code>null</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>&quot;hybrid&quot;</code> | <code>null</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;remote&quot;</code> | <code>null</code> |
| dev | <code>&quot;48365334&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |

### Config W (7)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46869120&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;47220989&quot;</code> | <code>&quot;hybrid&quot;</code> | <code>null</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>&quot;remote&quot;</code> | <code>null</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;47980297&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>&quot;remote&quot;</code> | <code>null</code> |

### Config F (6)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46869120&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>&quot;hybrid&quot;</code> | <code>&quot;onsite&quot;</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |
| dev | <code>&quot;48021354&quot;</code> | <code>&quot;hybrid&quot;</code> | <code>&quot;remote&quot;</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>&quot;remote&quot;</code> | <code>&quot;hybrid&quot;</code> |

## seniority

### Config B (6)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46959004&quot;</code> | <code>&quot;junior&quot;</code> | <code>null</code> |
| dev | <code>&quot;47673074&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;47986820&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;48804695&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |

### Config C (13)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46863917&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;46888712&quot;</code> | <code>&quot;senior&quot;</code> | <code>null</code> |
| dev | <code>&quot;46893914&quot;</code> | <code>&quot;staff+&quot;</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;47673074&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>&quot;senior&quot;</code> | <code>null</code> |
| dev | <code>&quot;47986820&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;senior&quot;</code> | <code>null</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;48804695&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;48819370&quot;</code> | <code>&quot;senior&quot;</code> | <code>null</code> |

### Config D (8)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46870506&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;46893914&quot;</code> | <code>&quot;staff+&quot;</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;46959004&quot;</code> | <code>&quot;junior&quot;</code> | <code>null</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;47976872&quot;</code> | <code>&quot;senior&quot;</code> | <code>null</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;48804695&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |

### Config E (9)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46893914&quot;</code> | <code>&quot;staff+&quot;</code> | <code>null</code> |
| dev | <code>&quot;47220091&quot;</code> | <code>&quot;senior&quot;</code> | <code>null</code> |
| dev | <code>&quot;47220989&quot;</code> | <code>&quot;junior&quot;</code> | <code>null</code> |
| dev | <code>&quot;47223968&quot;</code> | <code>&quot;senior&quot;</code> | <code>null</code> |
| dev | <code>&quot;47986820&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;48362254&quot;</code> | <code>&quot;senior&quot;</code> | <code>null</code> |
| dev | <code>&quot;48376486&quot;</code> | <code>&quot;staff+&quot;</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;48804695&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |

### Config W (7)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46893914&quot;</code> | <code>&quot;staff+&quot;</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;46959004&quot;</code> | <code>&quot;junior&quot;</code> | <code>null</code> |
| dev | <code>&quot;47220091&quot;</code> | <code>&quot;senior&quot;</code> | <code>null</code> |
| dev | <code>&quot;47220989&quot;</code> | <code>&quot;junior&quot;</code> | <code>null</code> |
| dev | <code>&quot;48376486&quot;</code> | <code>&quot;staff+&quot;</code> | <code>null</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |

### Config F (15)

| Split | Post / label ID | Label value | Model value |
| --- | --- | --- | --- |
| dev | <code>&quot;46863917&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;46870506&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;46875351&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;46893914&quot;</code> | <code>&quot;staff+&quot;</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;47220599&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;47232351&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;47241526&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;47256159&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;47308369&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;47632126&quot;</code> | <code>&quot;senior&quot;</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;47979394&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;48376486&quot;</code> | <code>&quot;staff+&quot;</code> | <code>&quot;senior&quot;</code> |
| dev | <code>&quot;48752786&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;48794583&quot;</code> | <code>null</code> | <code>&quot;staff+&quot;</code> |
| dev | <code>&quot;48804695&quot;</code> | <code>null</code> | <code>&quot;senior&quot;</code> |

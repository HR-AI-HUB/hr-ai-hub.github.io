# Minor Data + AI-driven Healthcare Innovation 2026-2027

## Inhoudsopgave

- [Positionering](#positionering)
- [Doel van de minor](#doel-van-de-minor)
- [Overzichtstabel minor](#overzichtstabel-minor)
- [Inhoudelijke themalijnen](#inhoudelijke-themalijnen)
- [Projecttypen binnen de minor](#projecttypen-binnen-de-minor)
- [Competenties en leeruitkomsten](#competenties-en-leeruitkomsten)
- [Werkvormen](#werkvormen)
- [Technische referentiearchitectuur](#technische-referentiearchitectuur)
- [Technische details per bouwblok](#technische-details-per-bouwblok)
- [Voorbeeld van een end-to-end projectflow](#voorbeeld-van-een-end-to-end-projectflow)
- [Beoogde deliverables per project](#beoogde-deliverables-per-project)
- [Randvoorwaarden voor uitvoering](#randvoorwaarden-voor-uitvoering)
- [Relatie met de HR AI-Hub](#relatie-met-de-hr-ai-hub)
- [Samenvatting UbiOps SHDG Pipeline en informatiebeveiliging](#samenvatting-ubiops-shdg-pipeline-en-informatiebeveiliging)
- [Samenvatting](#samenvatting)
- [License](#license)

## Positionering

De minor **Data + AI-driven Healthcare Innovation** richt zich op het ontwerpen, valideren en implementeren van data- en AI-oplossingen voor zorg, welzijn en zorgtechnologie. De minor sluit aan op de werkwijze van het HR Datalab Healthcare en gebruikt een gestandaardiseerde projectaanpak waarin **intake, governance, data-architectuur, AI-workflows, validatie en implementatie** integraal zijn georganiseerd.

De inhoud van deze minor is gebaseerd op de beschikbare projectinformatie in de map **MINOR_CMI_Data + AI-driven Healthcare Innovation** en op de technische en organisatorische patronen zoals uitgewerkt in de projectrepository **RESEARCH_SUPPORT/PROJECTS**. Daardoor is de minor niet alleen inhoudelijk onderwijsgericht, maar ook direct verbonden met een uitvoerbare onderzoeks- en implementatiepraktijk.

---

## Doel van de minor

De minor leidt studenten op om in multidisciplinaire teams te werken aan concrete zorgvraagstukken waarin data, AI, generatieve AI, workflow-automatisering en digitale infrastructuur samenkomen. Studenten leren niet alleen modellen of dashboards bouwen, maar vooral hoe zij een oplossing verantwoord en reproduceerbaar kunnen ontwikkelen binnen de randvoorwaarden van privacy, informatiebeveiliging, klinische bruikbaarheid en technische schaalbaarheid.

De minor heeft vier hoofddoelen:

1. Het analyseren van zorgvraagstukken en het vertalen daarvan naar een technisch en organisatorisch uitvoerbaar project.
2. Het ontwerpen van veilige data- en AI-workflows voor zorgcontexten.
3. Het bouwen en testen van prototypes met onder meer RAG, agentic workflows, dashboards, databases en cloud- of containerinfrastructuur.
4. Het opleveren van implementeerbare resultaten inclusief documentatie, validatie en overdraagbaarheid naar praktijkpartners.

---

## Overzichtstabel minor

| Onderdeel | Inhoud | Typische output | Technische componenten |
| --- | --- | --- | --- |
| Intake en scoping | Verhelderen van zorgvraag, databeschikbaarheid, stakeholders, risico's en randvoorwaarden | intakeformulier, projectcanvas, risicoanalyse | intake-procedure, governance, AVG-check, data-classificatie |
| Data-acquisitie en voorbereiding | Verzamelen, structureren, anonimiseren of pseudonimiseren van data | opgeschoonde datasets, markdown, csv/json/sql bronnen | PDF-naar-Markdown, databases, ETL, Python, SQL |
| AI- en workflowontwerp | Ontwerpen van RAG-, agent- of beslisondersteunende workflows | workflowdiagram, promptontwerp, architectuurschets | Flowise, Langflow, LangChain, Azure OpenAI, Ollama |
| Prototypeontwikkeling | Bouwen van een werkend prototype voor analyse, synthese, triage, documentverwerking of simulatie | demo, API, dashboard, agentflow, notebook | Docker, Python, Node.js, MSSQL/MySQL/Postgres, vector store |
| Validatie en benchmarking | Toetsen op kwaliteit, bruikbaarheid, veiligheid en reproduceerbaarheid | benchmarkrapport, evaluatie, gebruikersfeedback | corpus metrics, document metrics, human-in-the-loop review |
| Implementatie en overdracht | Voorbereiden van beheer, documentatie en opschaling | handleiding, deploymentplan, overdrachtsdossier | SURF/SRAM, Traefik, HTTPS, container deployment, monitoring |

---

## Inhoudelijke themalijnen

### 1. Data science voor zorg en welzijn

Studenten werken met zorgdata in verschillende vormen: tekst, tabellen, vragenlijsten, sensordata, procesdata en documentatie. De focus ligt op datakwaliteit, semantiek, herleidbaarheid en verantwoord hergebruik. Daarbij wordt expliciet aandacht besteed aan het verschil tussen ruwe data, bewerkte data, pseudonieme data en synthetische data.

### 2. Generatieve AI en agentic workflows

Binnen de minor worden generatieve AI-toepassingen niet benaderd als losse chatinterfaces, maar als **modulaire workflows**. De projectvoorbeelden in RESEARCH_SUPPORT laten zien dat een bruikbare zorgtoepassing meestal bestaat uit meerdere stappen, zoals:

1. documentinname;
2. extractie en conversie;
3. pseudonimisering;
4. retrieval of kennisverrijking;
5. generatie of classificatie;
6. evaluatie en menselijke controle.

Deze opbouw sluit aan op projecten rond **Generative Agent based Data Synthesis**, **Langflow op SURF**, **Flowise-workflows**, **Azure OpenAI-integratie** en **RAG-toepassingen**.

### 3. Digitale infrastructuur en deployment

De minor behandelt niet alleen modelgebruik, maar ook de infrastructuur die nodig is om AI-oplossingen veilig beschikbaar te maken. Voorbeelden uit de projectrepository tonen een consistente stack met:

- Docker-gebaseerde deployments;
- reverse proxy via Traefik;
- HTTPS via Let's Encrypt;
- persistente opslag via PostgreSQL of SQLite;
- identity en toegangsbeheer via SRAM/SURF;
- cloudkoppelingen met Azure OpenAI;
- lokale of privacy-first alternatieven via Ollama of on-prem omgevingen.

### 4. Implementatie in de zorgpraktijk

De minor is praktijkgericht. Dat betekent dat elk project niet alleen technisch moet werken, maar ook moet passen binnen werkprocessen van zorgprofessionals. Studenten leren daarom ontwerpen voor uitlegbaarheid, overdraagbaarheid, gebruikersacceptatie en organisatorische inbedding.

---

## Projecttypen binnen de minor

Op basis van de beschikbare projectinformatie en de RESEARCH_SUPPORT-projectstructuur kunnen minorprojecten worden ondergebracht in de volgende categorieen.

| Projecttype | Beschrijving | Voorbeelden van technieken |
| --- | --- | --- |
| Clinical document AI | Verwerken, structureren, samenvatten of synthetiseren van klinische documentatie | GPT-4.1, prompt engineering, pseudonimisering, markdown pipelines |
| RAG en kennisassistenten | Antwoorden genereren op basis van richtlijnen, protocollen of lokale kennisbronnen | Flowise, Langflow, embeddings, vector store, SQLite memory |
| Data-integratie en databases | Koppelen van zorgtaxonomieen, registraties of operationele databronnen | MSSQL, MySQL, Python connectors, ETL |
| Digital twins en simulatie | Modelleren van processen, patientpaden of beslissituaties | dashboards, simulatie, event/data pipelines |
| Monitoring en observability | Inzicht geven in prestaties, gebruik en betrouwbaarheid van systemen | Prometheus, Grafana, logging, metrics |
| Synthetic data en privacy-preserving AI | Genereren van synthetische dossiers of datasets voor onderzoek en onderwijs | agent-based synthesis, benchmarking, privacy-preserving workflows |

---

## Technische referentiearchitectuur

De minor gebruikt een referentiearchitectuur die is afgeleid van de projectpatronen in de repository. Deze architectuur is modulair en kan per project lichter of zwaarder worden ingevuld.

### Laag 1. Intake, governance en toegang

- intakeprocedure voor nieuwe projecten;
- toetsing op AVG, ethiek, dataminimalisatie en doelbinding;
- rolverdeling tussen opdrachtgever, onderzoeker, student en technisch beheer;
- toegangsbeheer via SURF/SRAM of afgeschermde projectomgevingen.

### Laag 2. Data-ingestie en opslag

- brondata uit PDF, markdown, csv, json, sql of vragenlijsten;
- documentconversie naar machineleesbare formaten;
- opslag in relationele databases, object storage of projectmappen;
- scheiding tussen brondata, bewerkte data en output-artifacts.

### Laag 3. AI- en workflowlaag

- orchestratie via Flowise of Langflow;
- LLM-koppelingen via Azure OpenAI;
- optionele lokale inferentie via Ollama;
- RAG met chunking, embeddings en retrieval;
- agent memory via SQLite of vergelijkbare persistente opslag.

### Laag 4. Applicatie- en servicelaag

- webtoegang via HTTPS;
- containerized services met Docker Compose;
- reverse proxy met Traefik;
- API-koppelingen voor hergebruik in dashboards of portals;
- gebruikersbeheer voor docent-, student- en partnerrollen.

### Laag 5. Validatie, monitoring en overdracht

- benchmarken van outputkwaliteit;
- logging en monitoring;
- documentatie van prompts, configuratie en deployment;
- overdracht naar praktijkpartner of volgende studentengroep.

---

## Technische details per bouwblok

### Azure OpenAI

Binnen meerdere projectvoorbeelden wordt Azure OpenAI gebruikt als enterprise-grade modelvoorziening. Voor de minor betekent dit dat studenten leren werken met:

- endpoint, API key en deployment name;
- modeldeployments voor chat en embeddings;
- beveiligde toegang via afgeschermde omgevingen;
- inzet voor documentconversie, classificatie, synthese en RAG.

### Flowise en Langflow

De repository laat zien dat low-code AI-orchestratie een belangrijke versneller is voor onderwijs en praktijk. Relevante technische kenmerken zijn:

- visueel ontwerpen van workflows;
- importeerbare chatflows;
- koppeling met Azure OpenAI-credentials;
- document loaders, chunkers, vector stores en memory componenten;
- inzet als webtoegankelijke inference endpoint.

### Docker, Traefik en PostgreSQL

Voor deployment op SURF- of Ubuntu-VM's wordt een patroon gebruikt met:

- Docker Compose voor multi-service deployment;
- Traefik als reverse proxy;
- poorten 80, 443 en optioneel 8080 voor beheer;
- automatische HTTPS-redirect en Let's Encrypt-certificaten;
- PostgreSQL voor persistente opslag van Langflow-data;
- volumes voor data, cache en browser/tooling artifacts.

### Databases en koppelingen

Voor zorginhoudelijke projecten is database-integratie essentieel. In de projectvoorbeelden komen onder meer voor:

- MSSQL in Docker voor verpleegkundige taxonomieen en kennisbanken;
- MySQL-koppelingen;
- Python-drivers en containerafhankelijke dependencies;
- SQL-gebaseerde ontsluiting van gestructureerde kennis voor AI-workflows.

### Synthetic data en benchmarking

De projecten rond generatieve data-synthese laten een volwassen workflow zien waarin studenten kunnen leren werken met:

- PDF naar Markdown conversie;
- pseudonimisering van klinische tekst;
- generatie van synthetische dossiers via supervisor/worker-agentstructuren;
- vergelijking tussen echte, gepseudonimiseerde en synthetische data;
- document- en corpusniveau metrics;
- human expert review als laatste kwaliteitscontrole.

---

## Voorbeeld van een end-to-end projectflow

Onderstaande flow vat de werkwijze van de minor samen en sluit direct aan op de projectpatronen uit RESEARCH_SUPPORT.

1. Een zorgpartner of docent brengt een vraagstuk in via de intake.
2. Het team bepaalt doel, datatoegang, risico's en gewenste output.
3. Beschikbare data worden verzameld en waar nodig geconverteerd naar bruikbare formaten.
4. Gevoelige data worden geanonimiseerd of gepseudonimiseerd.
5. Studenten ontwerpen een workflow in bijvoorbeeld Flowise of Langflow.
6. De workflow gebruikt een LLM, retrieval, tools en eventueel databases.
7. Het prototype wordt getest op inhoudelijke kwaliteit, technische stabiliteit en bruikbaarheid.
8. Resultaten worden gedocumenteerd en overdraagbaar gemaakt.
9. Indien relevant volgt deployment op een afgeschermde SURF- of cloudomgeving.

---

## Competenties en leeruitkomsten

Na afronding van de minor kan de student:

1. Een zorgvraag vertalen naar een data- en AI-project met heldere scope, randvoorwaarden en succescriteria.
2. Een verantwoorde dataworkflow ontwerpen waarin privacy, governance en reproduceerbaarheid zijn geborgd.
3. AI-componenten zoals LLM's, RAG, agentflows en databases combineren tot een werkend prototype.
4. Technische keuzes onderbouwen op basis van veiligheid, schaalbaarheid, onderhoudbaarheid en klinische bruikbaarheid.
5. Resultaten valideren met zowel technische metrics als feedback van domeinexperts.
6. Een oplossing documenteren en overdragen aan stakeholders in onderwijs, onderzoek of praktijk.

---

## Werkvormen

De minor combineert onderwijs, onderzoek en praktijkontwikkeling in de volgende werkvormen:

- projectonderwijs in multidisciplinaire teams;
- technische labs en hands-on workshops;
- ontwerp- en validatiesessies met zorgpartners;
- sprintreviews en demo's;
- documentatie en overdracht als vast onderdeel van de oplevering.

---

## Beoogde deliverables per project

Elk minorproject levert minimaal de volgende onderdelen op:

| Deliverable | Toelichting |
| --- | --- |
| Projectintake en scope | probleemdefinitie, stakeholders, randvoorwaarden, risico's |
| Architectuur en workflowontwerp | functioneel en technisch ontwerp van de oplossing |
| Werkend prototype | aantoonbare demonstrator of proof of concept |
| Datadocumentatie | beschrijving van bronnen, bewerkingen en beperkingen |
| Validatie | testresultaten, benchmark of expertfeedback |
| Implementatieadvies | advies voor opschaling, beheer en vervolg |
| Overdrachtsdossier | handleiding, configuratie, lessons learned |

---

## Randvoorwaarden voor uitvoering

Voor een succesvolle uitvoering van de minor zijn de volgende randvoorwaarden van belang:

- toegang tot een veilige ontwikkelomgeving;
- duidelijke afspraken over datagebruik en privacy;
- beschikbaarheid van praktijkcases;
- begeleiding op zowel technisch als zorginhoudelijk vlak;
- inzet van student-assistenten voor onboarding en dagelijkse ondersteuning, zodat studenten snel wegwijs worden in de gehanteerde veilige cloudwerkomgeving;
- gebruik van een samenhangende veilige werkomgeving op basis van SURF Research Drive, SURF Research Cloud en de operationele know-how van het Datalab Healthcare;
- aanvullende ondersteuning vanuit RPS, in het bijzonder via Elly Katoen, senior datasteward binnen Dienst RPS;
- herbruikbare projecttemplates, intakeformats en deploymentpatronen.

---

## Relatie met de HR AI-Hub

De **HR AI-Hub** past logisch binnen deze minor als voorbeeld van een veilige en toekomstbestendige AI-voorziening voor onderwijs, onderzoek en praktijkgericht innoveren. De AI-Hub is ontwikkeld in samenwerking met **SURF** en sluit aan op publieke waarden zoals autonomie, menselijkheid en rechtvaardigheid. Voor studenten maakt dit concreet zichtbaar dat werken met generatieve AI in de zorg niet alleen draait om modelkwaliteit, maar ook om verantwoorde toegang, veilige infrastructuur en duidelijke organisatorische kaders.

Voor de minor is de HR AI-Hub relevant op drie niveaus. Ten eerste biedt de hub een **veilige experimenteeromgeving** waarin met grote taalmodellen kan worden gewerkt binnen een gecontroleerde cloudcontext. Ten tweede laat de hub zien hoe **onderwijs, onderzoek en datalabs** met elkaar verbonden kunnen worden in een gedeelde infrastructuur. Ten derde maken de beschikbare showcases duidelijk hoe AI-toepassingen daadwerkelijk kunnen landen in concrete projecten, zoals transcriptie, research support, agentic workflows en onderwijsassistenten.

Ook didactisch is de HR AI-Hub van waarde. Studenten kunnen leren dat modelkeuze afhankelijk is van het doel van een project: sommige toepassingen vragen om tekstgeneratie, andere om embeddings, spraakherkenning, multimodale analyse of codeondersteuning. De HR AI-Hub laat zien dat zo'n modelportfolio niet los staat van de praktijk, maar onderdeel is van een bredere leeromgeving met onboarding, support, documentatie en afspraken over veilig gebruik.

Binnen het geheel van deze minor kan de HR AI-Hub daarom worden gezien als een **institutioneel en technisch referentiekader**: een omgeving waarin studenten ervaring opdoen met moderne AI-tools, terwijl zij tegelijk leren werken binnen professionele randvoorwaarden voor zorg, onderzoek en onderwijs.

---

## Samenvatting UbiOps SHDG Pipeline en informatiebeveiliging

De documentatie van de **UbiOps SHDG Pipeline** laat zien hoe een onderzoeksworkflow voor synthetische zorgdata kan worden opgeschaald naar een beheersbare en veilig ingerichte MLOps-pipeline. De kern bestaat uit vier opeenvolgende stappen: **FLOW01** voor documentinname en parsing, **FLOW02** voor pseudonimisering of privacy masking, **FLOW03** voor generatieve synthese van nieuwe fictieve dossiers, en **FLOW04** voor evaluatie van kwaliteit, semantische overeenkomst en privacyrisico. Deze opzet is relevant voor de minor omdat zij een concreet voorbeeld biedt van hoe studenten een AI-workflow niet alleen inhoudelijk, maar ook technisch en organisatorisch verantwoord kunnen opbouwen.

Een belangrijk uitgangspunt in deze pipeline is de scheiding tussen brondata, verwerkte data en synthetische output. De bronbestanden staan in **SURF Research Drive** en worden niet publiek gedeeld, niet opgenomen in repositories en niet structureel in deployment packages opgeslagen. Voor lokale ontwikkeling kan met gecontroleerde toegang worden gewerkt via een gemounte Research Drive-omgeving, terwijl in runtime-situaties bestanden just-in-time worden opgehaald binnen de container en daarna weer worden verwijderd. Daarmee wordt het principe van dataminimalisatie praktisch toegepast.

De UbiOps-uitwerking onderstreept daarnaast dat informatiebeveiliging geen losse eindcontrole is, maar vanaf het begin onderdeel moet zijn van het ontwerp. Voor bachelorstudenten is vooral van belang dat zij leren werken met duidelijke afspraken over toegang, datagebruik, versiebeheer, veilige opslag van sleutels en verantwoord omgaan met privacygevoelige informatie.

Voor de minor betekent dit dat studenten niet alleen leren een AI-prototype te bouwen, maar ook leren hoe zij dat op een zorgvuldige en professionele manier doen. De UbiOps SHDG Pipeline is daarmee een bruikbaar referentievoorbeeld voor projecten waarin zorgdata, generatieve AI, cloud deployment en verantwoord datagebruik samenkomen.

---

## Samenvatting

De minor **Data + AI-driven Healthcare Innovation 2026-2027** positioneert zich als een praktijkgerichte en technisch volwassen leeromgeving waarin studenten leren hoe zij zorginnovatie kunnen realiseren met data en AI. De minor onderscheidt zich doordat zij niet stopt bij analyse of modelgebruik, maar expliciet inzet op **end-to-end projectuitvoering**: van intake en governance tot workflowdesign, deployment, validatie en implementatie.

Door aan te sluiten op de projectstructuur van **RESEARCH_SUPPORT/PROJECTS** ontstaat een minor die direct bruikbaar is voor onderzoek, onderwijs en praktijkpartners, en die studenten voorbereidt op rollen waarin technische diepgang, verantwoord innoveren en domeinsensitiviteit samenkomen.

---

## License

This project is released under the [Creative Commons BY-ND 4.0](https://creativecommons.org/licenses/by-nd/4.0/legalcode.nl) licence, consistent with the HR AI-HUB Pilot programme.

**Developed by:** HR DataLab Healthcare · [SURF AI-Hub Pilot Programme 2025–2026](https://hr-ai-hub.github.io/)  
**Tech lead:** RFvdW · **DataLab coordinator:** Alfons Looman  
**Institution:** [Hogeschool Rotterdam](https://www.hogeschoolrotterdam.nl) · In collaboration with [SURF](https://www.surf.nl) & [Npuls](https://www.surf.nl/themas/artificial-intelligence/projecten-en-samenwerkingen/ai-hub)

# Begroten Azure en Visual Studio Enterprise voor HR DataLabs 2027

**Datum:** 4 september 2026  
**Status:** concept voor interne begroting en afstemming met HR/ICT/IDT  
**Scope:** HR DataLab Healthcare, HR AI Hub en AI-SUStech

## Inhoudsopgave

- [1. Samenvatting](#1-samenvatting)
- [2. Context en uitgangspunten](#2-context-en-uitgangspunten)
- [3. Beheerst gebruik van Azure en Visual Studio](#3-beheerst-gebruik-van-azure-en-visual-studio)
- [4. Data, privacy en verantwoord gebruik](#4-data-privacy-en-verantwoord-gebruik)
- [5. Bronnen](#5-bronnen)
- [Bijlage A - Geanonimiseerde deelnemers](#bijlage-a---geanonimiseerde-deelnemers)
- [Bijlage B - Uitgevoerde prompt](#bijlage-b---uitgevoerde-prompt)
- [Bijlage C - LLM-modelinventaris uit screenshot](#bijlage-c---llm-modelinventaris-uit-screenshot)

## 1. Samenvatting

De HR DataLabs leiden Data Scientists op in het verantwoord gebruik van online cloud-AI via Azure Foundry. De toegang tot Azure Foundry LLM's verloopt via enterprise-licenties. De lokale ontwikkelomgeving bestaat uit Visual Studio Code in combinatie met Foundry Toolkit en GitHub Copilot Education.

Deze combinatie ondersteunt onderzoek, onderwijs, experimenten, prototyping en kennisopbouw binnen AI-SUStech, HR DataLab Healthcare en de HR AI Hub. De continuiteit van de relevante licenties en toegangsrechten is daarom een randvoorwaarde voor de innovatiekracht van alle DataLabs. De bestaande Azure-tenant loopt via SURF; de precieze contractuele en licentievoorwaarden moeten door HR/ICT/IDT worden bevestigd.

Afhankelijk van de gegevensclassificatie, het vereiste beschermingsniveau en de toepasselijke regelgeving kan voor Azure Foundry gebruik worden gemaakt van Global Standard of Data Zone Standard. Een Data Zone kan in de Verenigde Staten of binnen de Europese Unie worden gekozen, bijvoorbeeld Sweden Central, wanneer dit door de dienst wordt ondersteund en de verwerking daar rechtmatig en organisatorisch is toegestaan.


## 2. Context en uitgangspunten

De gecontroleerde inzet sluit aan op de geraadpleegde DataLab-bronnen:

- het DataLab is een eerste aanspreekpunt voor intake, methodologische vragen en data-/softwarekeuzes;
- projecten worden gefaseerd uitgevoerd: voorfase, PoC, dataverzameling, analyse en overdracht;
- een digitale workspace bestaat uit infrastructuur, toegang, data, verwerking, analyse en output/overdracht;
- de voorkeursinrichting is hybride: lokaal waar controle en privacy leidend zijn, cloud of SURF waar schaalbare capaciteit nodig is;
- keuzes worden vastgelegd in onder meer een onderzoeksprotocol, analyseplan, Data Management Plan (DMP) en Software Management Plan (SMP);
- het DataLab verwijst door naar ICT/IDT, privacy/security, datastewards, methodologen of domeinexperts wanneer formele of specialistische afstemming nodig is.

De HR AI Hub fungeert in deze context als project- en kennisomgeving voor AI-experimenten, notebooks en demonstrators. De map `PROJECTS` van `RESEARCH_SUPPORT` laat een brede verzameling afgebakende projecten zien, waaronder Azure/OpenAI, Langflow, monitoring, digitale twins, datasynthetisering en intakeprocedures. Die projectmatige structuur ondersteunt opleiding en beheerst gebruik van bestaande voorzieningen.



## 3. Beheerst gebruik van Azure en Visual Studio

### Azure

Azure wordt binnen de bestaande inrichting primair gebruikt voor online toegang tot Azure Foundry LLM's. Azure compute wordt alleen ingezet wanneer dit rechtstreeks noodzakelijk is voor de geselecteerde Foundry-workload. Andere kostengevoelige Azure-services worden niet standaard gebruikt en alleen na expliciete goedkeuring ingezet wanneer zij strikt noodzakelijk zijn.

### Visual Studio Code, Foundry Toolkit en GitHub Copilot Education

Data Scientists worden opgeleid met een hybride ontwikkelmodel:

- Visual Studio Code wordt lokaal gebruikt voor ontwikkeling, testen, documentatie en versiebeheer;
- Foundry Toolkit ondersteunt de lokale verbinding met en ontwikkeling voor Azure Foundry;
- GitHub Copilot Education ondersteunt het leren programmeren, documenteren, testen en ontwikkelen, voor zover de organisatie en gebruikers hiervoor gerechtigd zijn;
- Azure Foundry wordt online gebruikt voor de noodzakelijke LLM-experimenten en gecontroleerde prototyping.

Deze werkwijze maakt het mogelijk om lokale voorbereiding en tests te combineren met gerichte toegang tot cloudmodellen. De DataLabs hoeven daardoor geen volledige Azure-infrastructuur voor iedere deelnemer in te richten.

Per project of opleidingsactiviteit wordt minimaal vastgelegd:

- doel, eigenaar en einddatum;
- dataclassificatie en toegestane omgeving;
- benodigde Foundry-functionaliteit en toegangsrechten;
- verantwoordelijke eigenaar en toegestane omgeving;
- bestaande licentieafspraken, gebruiksgrenzen en stopcriteria;
- logging, toegangsrollen en overdracht/afsluiting.

### Visual Studio Enterprise

Visual Studio Enterprise kan worden ingezet voor ontwikkeling, testen, versiebeheer en reproduceerbare software-workflows die nodig zijn voor de Azure Foundry-werkomgeving. De licentie is geen automatisch recht op onbeperkte Azure-capaciteit. Eventuele Azure-tegoeden, testrechten, cloudvoordelen en gebruikersvoorwaarden moeten afzonderlijk worden geverifieerd.

Gebruik Visual Studio primair voor:

- lokale ontwikkeling en debugging;
- lokale testomgevingen met synthetische of openbare data;
- documentatie, versiebeheer en pull requests;
- gecontroleerde ontwikkeling en testen voor Azure Foundry;
- lokale voorbereiding voordat een Foundry-workload online wordt uitgevoerd.

### Kosteneffectief opleidings- en ontwikkelmodel

De kosteneffectiviteit ontstaat doordat de DataLabs lokale ontwikkeling en voorbereiding combineren met gerichte online toegang tot Azure Foundry. Azure compute wordt alleen gebruikt in directe relatie tot de Foundry-workload. Andere kostengevoelige Azure-services, zoals permanente opslag, databases, GPU-infrastructuur, uitgebreide netwerken of permanente endpoints, worden niet standaard geactiveerd.

Een andere Azure-service wordt alleen ingezet wanneer deze aantoonbaar strikt noodzakelijk is, vooraf is onderbouwd en door de bevoegde HR/ICT/IDT-verantwoordelijke is goedgekeurd. Hierdoor kunnen veel Data Scientists worden opgeleid met bestaande licenties en lokale hulpmiddelen, terwijl het betaalde cloudgebruik beperkt blijft tot de noodzakelijke Foundry-functionaliteit.

### Indicatieve jaarlijkse kosten voor IDT

Bijlage A bevat momenteel 13 deelnemers. Het deelnemersaantal alleen is onvoldoende om de daadwerkelijke jaarfactuur vast te stellen. Voor een betrouwbare IDT-begroting moet worden gerekend met de contractprijs per gebruiker, het werkelijke Azure Foundry-verbruik en eventuele reeds beschikbare licenties.

| Kostencomponent | Rekenbasis voor 13 deelnemers | Opmerking |
|---|---:|---|
| Visual Studio Enterprise | `13 x jaarlijkse contractprijs per gebruiker` | Prijs en eventuele SURF-/HR-korting nader te verifiëren. |
| GitHub Copilot Education | `13 x €0`, indien alle gebruikers gerechtigd zijn | Alleen kosteloos bij geldige onderwijsrechten en binnen de toepasselijke voorwaarden. |
| Azure Foundry LLM's | werkelijk tokenverbruik, input en output | Niet af te leiden uit het aantal deployments of de weergegeven capaciteit. |
| Embeddings | werkelijk aantal verwerkte tokens | Alleen relevant wanneer `text-embedding-3-large` daadwerkelijk wordt gebruikt. |
| Azure compute | werkelijk aantal compute-uren | Alleen opnemen wanneer deze rechtstreeks noodzakelijk is voor een Foundry-workload. |
| Overige Azure-services | standaard `€0` | Alleen opnemen na expliciete noodzaak en goedkeuring. |

De indicatieve jaarlijkse IDT-kosten zijn daarmee: `13 x Visual Studio Enterprise-contractprijs + werkelijk Azure Foundry-verbruik + eventueel goedgekeurde compute`. Een exact eurobedrag is pas verantwoord nadat IDT de contractprijs per Visual Studio Enterprise-gebruiker, de licentiestatus van de 13 deelnemers en het verwachte Foundry-verbruik heeft bevestigd. De modelcapaciteiten in Bijlage C zijn technische deploymentgegevens en mogen niet als jaarlijkse kosten worden geïnterpreteerd.

### Regionale inzet en compliance

De keuze tussen Global Standard en Data Zone Standard wordt bepaald door de aard en gevoeligheid van de data, de eisen rond dataresidentie en doorgifte, contractuele afspraken en de toepasselijke AVG/GDPR-, NIS2- en EU AI Act-beoordeling. Voor openbare, synthetische of laag-risico testdata kan een goedgekeurde Global Standard of Data Zone worden gebruikt. Voor gevoelige Europese onderzoeksdata heeft een goedgekeurde EU Data Zone, bijvoorbeeld Sweden Central, de voorkeur wanneer de benodigde Foundry-modellen en functies daar beschikbaar zijn.

Een Amerikaanse Data Zone wordt alleen gebruikt wanneer de data, het onderzoeksdoel, de contracten en de compliancebeoordeling dit toestaan. Voor gezondheidsgegevens of andere bijzondere persoonsgegevens is vooraf formele intake, dataclassificatie en goedkeuring nodig. Global Standard, een Amerikaanse Data Zone of Sweden Central garandeert op zichzelf geen volledige AVG-, NIS2- of EU AI Act-compliance. De actuele Azure Foundry-documentatie, modelvoorwaarden, dataresidentie, regionale beschikbaarheid en organisatorische maatregelen moeten daarom worden geverifieerd.

## 4. Data, privacy en verantwoord gebruik

Gebruik een individuele ontwikkelomgeving alleen voor openbare, synthetische of aantoonbaar geanonimiseerde testdata. Plaats geen echte gezondheidsgegevens, persoonsgegevens, patiëntinformatie, onderzoeksdata met verhoogd risico of vertrouwelijke partnerdata in een persoonlijke Visual Studio/Azure-sandbox.

Bij gevoelige data volgt eerst intake, classificatie en afstemming met de juiste privacy/security- en datamanagementrollen. Afhankelijk van het risico kan een TRE, SURF-omgeving of andere goedgekeurde researchomgeving nodig zijn. De cloudkeuze wordt niet uitsluitend op prijs of technische voorkeur bepaald.

Escalatie is verplicht bij:

- nieuwe persoonsgegevens of gezondheidsgegevens;
- toevoeging van externe partners of nieuwe cloudleveranciers;
- overgang van PoC naar operationeel of productieachtig gebruik;
- onduidelijkheid over licenties, datadeling, eigenaarschap of publicatie;
- gebruik van andere Azure-services dan Azure Foundry;
- onverwachte kosten of risico voor de continuïteit van licenties en toegangsrechten.

## 5. Bronnen

- [Statuut HR Healthcare DataLab](https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/tree/main/PROJECTS/STATUUT)
- [DataLab Healthcare](https://hr-datalab-healthcare.github.io/)
- [HR AI Hub](https://github.com/HR-AI-HUB/hr-ai-hub.github.io)
- [RESEARCH_SUPPORT - PROJECTS](https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/tree/main/PROJECTS)

De bronnen ondersteunen de governance-, triage-, hybride infrastructuur- en datamanagementprincipes. Zij bevestigen geen concrete Azure Enterprise Agreement-prijzen, Visual Studio Enterprise-tegoeden of HR-licentievoorwaarden.

## Bijlage A - Geanonimiseerde deelnemers

| Deelnemer | UPN | E-mail |
|---|---|---|
| Deelnemer 01 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 02 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 03 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 04 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 05 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 06 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 07 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 08 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 09 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 10 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 11 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 12 | [UPN verwijderd] | [e-mailadres verwijderd] |
| Deelnemer 13 | [UPN verwijderd] | [e-mailadres verwijderd] |

## Bijlage B - Uitgevoerde prompt

```text
Pas het Markdown-bestand aan:

[lokaal bronbestand verwijderd]

Gebruik de actuele inhoud van het bestand als uitgangspunt en behoud bestaande wijzigingen die niet strijdig zijn met deze opdracht.

Verwijder hoofdstuk `## 4. Continuïteit en kostenbeheersing` volledig en werk de inhoudsopgave en hoofdstuknummering bij.

Beschrijf als centraal uitgangspunt dat de HR DataLabs Data Scientists opleiden in het verantwoord gebruik van online cloud-AI via Azure Foundry. De toegang tot Azure Foundry LLM's verloopt via enterprise-licenties. De lokale ontwikkelomgeving bestaat uit Visual Studio Code in combinatie met Foundry Toolkit en GitHub Copilot Education.

Beschrijf Azure uitsluitend vanuit het perspectief van toegang tot Azure Foundry LLM's. Azure compute wordt alleen ingezet wanneer dit rechtstreeks noodzakelijk is voor de geselecteerde Foundry-workload. Andere kostengevoelige Azure-services, zoals permanente opslag, databases, GPU-infrastructuur, uitgebreide netwerken en permanente endpoints, worden niet standaard gebruikt. Zij zijn alleen toegestaan wanneer ze aantoonbaar strikt noodzakelijk zijn en vooraf zijn goedgekeurd.

Leg uit waarom deze hybride werkwijze kosteneffectief is: Data Scientists ontwikkelen, testen en bereiden lokaal voor met Visual Studio Code, Foundry Toolkit en GitHub Copilot Education. Alleen de noodzakelijke LLM-experimenten en Foundry-workloads worden online uitgevoerd. Daardoor is geen volledige Azure-infrastructuur voor iedere deelnemer nodig.

Beschrijf de bijdrage aan onderwijs, onderzoek, prototyping, kennisopbouw en innovatie binnen AI-SUStech, HR DataLab Healthcare en de HR AI Hub.

Beschrijf dat de DataLabs, afhankelijk van de gegevensclassificatie, het vereiste beschermingsniveau en de toepasselijke regelgeving, gebruik kunnen maken van Global Standard en Data Zone Standard. Een Data Zone kan in de Verenigde Staten of binnen de Europese Unie worden gekozen, bijvoorbeeld Sweden Central, wanneer dit door de dienst wordt ondersteund en de verwerking daar rechtmatig en organisatorisch is toegestaan.

Leg uit dat de keuze tussen Global Standard en Data Zone Standard wordt bepaald door de aard en gevoeligheid van de data, AVG/GDPR, NIS2-gerelateerde eisen, de toepasselijkheid van de EU AI Act, contractuele afspraken en eisen rond dataresidentie en doorgifte.

Voeg een paragraaf toe met de titel `### Regionale inzet en compliance` en beschrijf daarin:

- openbare, synthetische of laag-risico testdata: Global Standard of een goedgekeurde Data Zone;
- gevoelige Europese onderzoeksdata: bij voorkeur een goedgekeurde EU Data Zone, bijvoorbeeld Sweden Central, mits de benodigde Foundry-modellen en functies daar beschikbaar zijn;
- Amerikaanse Data Zone: alleen wanneer de data, het onderzoeksdoel, de contracten en de compliancebeoordeling dit toestaan;
- gezondheidsgegevens of andere bijzondere persoonsgegevens: uitsluitend na formele intake, dataclassificatie en goedkeuring;
- onduidelijke gevallen: niet uitvoeren totdat HR/ICT/IDT en privacy/security een besluit hebben genomen.

Formuleer uitdrukkelijk dat Global Standard, een Amerikaanse Data Zone of Sweden Central op zichzelf geen volledige AVG-, NIS2- of EU AI Act-compliance garandeert. Controleer de actuele Azure Foundry-documentatie, modelvoorwaarden, dataresidentie en regionale beschikbaarheid.

Behoud de relevante privacy- en data-afspraken over openbare, synthetische of aantoonbaar geanonimiseerde testdata, voorafgaande dataclassificatie, goedgekeurde beveiligde onderzoeksomgevingen en escalatie bij privacy-, security-, licentie- of toegangsproblemen.

Laat in de verificatiepunten controleren welke enterprise-licenties, Azure Foundry-modellen, gebruikslimieten, Visual Studio-rechten, Foundry Toolkit-versies en GitHub Copilot Education-rechten van toepassing zijn. Controleer daarnaast Global Standard, Data Zone Standard, Sweden Central, de Amerikaanse Data Zone, dataresidentie, doorgifte en de benodigde AVG/GDPR-, NIS2- en EU AI Act-beoordelingen. Markeer onbevestigde informatie als “nader te verifiëren”.

Behoud Bijlage A met de deelnemerslijst en neem deze prompt op als Bijlage B.

Controleer dat hoofdstuk 4 volledig is verwijderd, dat de inhoudsopgave klopt, dat de tekst geen algemene Azure-infrastructuurbegroting suggereert, dat Global Standard en Data Zone Standard correct zijn opgenomen, dat Sweden Central als mogelijke EU-regio wordt genoemd en dat de Markdown syntactisch correct blijft.

Gebruik zakelijke, feitelijke en compacte formuleringen. Voeg geen nieuwe bedragen of onbevestigde licentieclaims toe.
```

## Bijlage C - LLM-modelinventaris uit screenshot

Onderstaande inventaris is overgenomen uit de aangeleverde screenshot van **Model deployments**. Alle weergegeven deployments hebben de status `Succeeded`.

| Modelnaam | Modelversie | Deployment type | Model retirement date | Capaciteit |
|---|---|---|---|---:|
| gpt-5-mini | 2025-08-07 | Global Standard | 9 februari 2027, 01:00 AM | 500 |
| gpt-chat-latest | 2026-05-05 | Global Standard | 5 oktober 2026, 02:00 AM | 2.000 |
| gpt-5.4 | 2026-03-05 | Data Zone Standard (EU: SWEDEN CENTRAL) | 2 september 2027, 02:00 AM | 252 |
| gpt-5.6-luna | 2026-07-09 | Global Standard | 11 januari 2028, 01:00 AM | 2.000 |
| gpt-5.6-sol | 2026-07-09 | Global Standard | 11 januari 2028, 01:00 AM | 1.000 |
| gpt-5.6-terra | 2026-07-09 | Global Standard | 11 januari 2028, 01:00 AM | 1.000 |
| gpt-oss-120b | 1 | Global Standard | 31 december 2099, 01:00 AM | N/A |
| Mistral-Large-3 | 1 | Global Standard | 31 december 2099, 01:00 AM | N/A |
| o3-mini | 2025-01-31 | Global Standard | 1 oktober 2026, 02:00 AM | 500 |
| text-embedding-3-large | 1 | Standard | 9 februari 2028, 01:00 AM | 350 |

**Opmerking:** de tabel is een momentopname uit de screenshot. Modelversies, retirementdatums, deployment types en capaciteiten moeten in Azure Foundry opnieuw worden gecontroleerd voordat zij voor planning, opleiding of compliancebesluiten worden gebruikt.

# A Prisma-aligned search engine for systematic literature reviews (SLR) driven by (WILLMA) SURF AI-HUB

## Contents

- [Scope](#scope)
- [Notebook & Code Development](#notebook--code-development)
- [Search Method](#search-method)
- [Relevance Ranking](#relevance-ranking)
- [Relevant Sources Found Through SLR](#relevant-sources-found-through-slr)
- [Reproducibility Notes](#reproducibility-notes)
- [Appendix A. Verantwoording en correcties](#appendix-a-verantwoording-en-correcties)
- [Appendix B. Reproducible Procedure and Code-Cell Explanation](#appendix-b-reproducible-procedure-and-code-cell-explanation)
- [Appendix C. Recipe: Reusing the Workflow for a New Clinical-Reasoning Topic](#appendix-c-recipe-reusing-the-workflow-for-a-new-clinical-reasoning-topic)

Generated: 2026-08-16 05:43 UTC

## Scope
A systematic literature review (SLR) is a structured method to find, screen, and summarize published research on a specific question using explicit search strategies and documented criteria.
The aim of SLR-Engine is to give anyone with a topic they want to explore — students and self-learners, researchers, business and consulting teams with a research question — an easy, lightweight way to do it, grounded in academic papers.
Less time, less effort, no methodology background required, but built on the same proven methodology that researchers around the world use.

For a detailed introduction on the original approach as created by Tui see https://github.com/HR-AI-HUB/hr-ai-hub.github.io/blob/main/SLR-ENGINE/docs/articles/introduction-to-slr-engine.md
The motivation behind building an *Open-source engine for running systematic literature review* is described here: https://github.com/tuirk/SLR-Engine/blob/main/docs/articles/why-i-built-slr-engine.md

**Topic:** An automated, AI-assisted systematic literature review addressing:

**The Problem With Using AI to Review AI-Written Code**

**Aim:** To synthesize empirical evidence on the reliability, risks, and forms of human oversight required when AI systems evaluate AI-generated code.

This custom-made implementation  [SLR-Engine](https://github.com/tuirk/SLR-Engine) separates retrieved evidence, AI-assisted advice, and the ranking used for inspection. Automated output does not replace scholarly judgement.

## Notebook & Code Development

The notebook uses [SLR-Engine](https://github.com/tuirk/SLR-Engine) for an auditable review workflow and a SURF AI-HUB Qwen 2.5 Instruct model only for bounded screening advice. It preserves literal queries, retrieval and deduplication results, reviewed decisions, lawful open-access retrieval, PDF validation, and exports in the SQLite-backed evidence trail.

Its supporting code was developed through collaboration between `gpt-5.6-Terra` and a Tech Lead, who authored the prompts and directed implementation and review. Human reviewers remain responsible for the workflow, configuration, scholarly use, and all final decisions.

### Why WILLMA Is Used

WILLMA is a controlled external service used only for a second, structured reading of one candidate during screening preparation. It does not search, retrieve, download, deduplicate, rank, write audit data, or decide inclusion or exclusion; those tasks remain in the local SQLite-backed SLR-Engine workflow.

The notebook reads its key from local `.env` configuration, discovers available models, and displays the selected model and token usage with the advice. It accepts only a visible text-based Qwen 2.5 Instruct model with at least 32 billion parameters. `SURF_AI_HUB_MODEL` can pin an eligible model; otherwise the largest eligible discovered model is selected.

### Local `.env` Configuration

Create a `.env` file in the repository root. It is local configuration only: do not commit it, attach it to reports, or paste its API-key value into notebooks.

```dotenv
# Required: obtain this value from the SURF AI-HUB service.
SURF_AI_HUB_API_KEY=replace-with-your-api-key

# Optional: pin an eligible visible Qwen 2.5 Instruct text model.
# Leave unset to let the notebook select the largest eligible discovered model.
SURF_AI_HUB_MODEL=Qwen/Qwen2.5-VL-32B-Instruct-AWQ
```

<details>
<summary>Environment parameter reference <sub>optional supporting detail</sub></summary>

| Parameter | Required | Purpose | Example value | 
| --- | --- | --- | --- |
| `SURF_AI_HUB_API_KEY` | Yes | Authenticates model-discovery and chat requests to SURF AI-HUB. | `replace-with-your-api-key` |
| `SURF_AI_HUB_MODEL` | No | Pins an eligible model visible to the supplied API key. If omitted, the notebook discovers and selects the largest eligible model. | `Qwen/Qwen2.5-VL-32B-Instruct-AWQ` |

</details>

### What WILLMA Actually Did

For the demonstration, the notebook sent only the first candidate's title and abstract, the review topic, and high-level criteria to WILLMA. It requested a tentative `Decision` (`include`, `exclude`, or `uncertain`), `Reason`, `Criteria`, and `Human review required: yes`.

The response, selected model, and token usage are displayed for inspection only. The advisory cell does not update the `screening` table or JSONL labels, and it does not download material. A human reviewer must evaluate I1-I3 and E1-E3, then separately commit any decision with a documented reason in `project.db`.

#### Where the WILLMA Output Appears

The notebook displays `recommendation_table` (`candidate_title`, `surf_ai_hub_model`, `surf_advisory`, and `human_decision_required`) and a token-usage table (`input_tokens`, `output_tokens`, and `total_tokens`). These are reviewer-facing notebook outputs, not database records. The following excerpt documents the retained executed output; it is not a committed label.

#### Recorded WILLMA Advisory Excerpt

The following is the retained output from the executed advisory cell for the candidate *Towards automating code review at scale*. The selected model was `Qwen/Qwen2.5-VL-32B-Instruct-AWQ`; the request used 368 input tokens and produced 79 output tokens (447 total). This is an advisory response, not a committed screening decision.

```text
Decision: include
Reason: The abstract describes an empirical study that evaluates the use of neural models for automating code review at scale. It includes systematic examination of model performance, dataset statistics, and challenges, meeting the inclusion criteria for empirical studies and evaluations.
Criteria: relevant inclusion IDs (empirical studies, benchmarks, systematic evaluations)
Human review required: yes
```

## Search Method

The notebook searched OpenAlex, Crossref, arXiv, and Semantic Scholar, capped at 25 source hits each. A source failure is an audit limitation, not evidence of no results.

### Literal Queries

<details>
<summary>Source-specific literal queries <sub>audit detail</sub></summary>

**OpenAlex**

```text
("AI code review" OR "LLM code review" OR "automated code review") AND ("AI-generated code" OR "generated code" OR "code generation")
```

**arXiv**

```text
(all:"code review" OR all:"automated code review") AND (all:"large language model" OR all:"AI generated code")
```

**Semantic Scholar**

```text
("AI code review" OR "LLM code review") AND ("AI-generated code" OR "code generation")
```

**Crossref**

```text
{
  "filter": {
    "type": "journal-article",
    "has-abstract": "true"
  },
  "query.bibliographic": [
    "AI code review",
    "large language model generated code"
  ]
}
```

</details>

### Retrieval and Processing Audit

<details>
<summary>Retrieval, screening, and download audit <sub>audit detail</sub></summary>

Canonical records after deduplication: **75**.

| Source | Distinct records |
| --- | --- |
| arxiv | 25 |
| crossref | 25 |
| openalex | 25 |

Title/abstract screening decisions are recorded with stated reasons and criteria in the project database.

| Decision | Records |
| --- | --- |
| exclude | 1 |
| include | 9 |

Download outcomes represent lawful open-access retrieval attempts only; publisher-blocked or closed content is not bypassed.

| Download status | Records |
| --- | --- |
| failed | 3 |
| skipped_closed | 1 |
| success | 5 |

</details>

## Relevance Ranking

Ranking is an inspection aid, not an inclusion decision. Score = number of matched topic terms + 4 for a committed title/abstract include decision + 2 for a verified downloaded open-access PDF. The rationale is listed for each paper.

<details>
<summary>Top 20 ranked records <sub>inspection aid</sub></summary>

| Rank | Paper | Evidence |
| --- | --- | --- |
| 1 | **Same Scrutiny, More Time: Eye Tracking Insights into Reviewing LLM-Labelled Code**<br>Khojah, R., Neto, F. G. d. O., Mohamad, M., Frattini, J., & Leitner, P. (2026) | **Score: 10**<br>matched: code review, llm, large language model, generated code; title/abstract included; open-access PDF downloaded<br>Sources: arxiv |
| 2 | **When AI Reviews Its Own Code: Recursive Self-Training Collapse in Code LLMs**<br>Song, X., Cai, Z., & Zhao, L. (2026) | **Score: 10**<br>matched: code review, llm, generated code, self-review; title/abstract included; open-access PDF downloaded<br>Sources: arxiv |
| 3 | **"Go Home Copilot, You're Drunk": Understanding Developer Responses to Agent-Generated Code Review Comments**<br>Cynthia, S. T., Widyasari, R., Roy, B., Zhang, T., & Lo, D. (2026) | **Score: 9**<br>matched: code review, generated code, agent-generated; title/abstract included; open-access PDF downloaded<br>Sources: arxiv |
| 4 | **Evaluating the Impact of Explainable AI on Trust in AI-Assisted Code Review**<br>Gao, Z., Barón, M. M. o., Habiba, U. e., Graziotin, D., & Wagner, S. (2026) | **Score: 9**<br>matched: code review, llm, large language model; title/abstract included; open-access PDF downloaded<br>Sources: arxiv |
| 5 | **From Human-Centric to Agentic Code Review: The Impact of Different Generations of Generative AI Technology on Review Quality**<br>Zhong, S., Noei, S., Adams, B., & Zou, Y. (2026) | **Score: 9**<br>matched: code review, llm, large language model; title/abstract included; open-access PDF downloaded<br>Sources: arxiv |
| 6 | **Fine-Tuning Large Language Models to Improve Accuracy and Comprehensibility of Automated Code Review**<br>Yu, Y., Rong, G., Shen, H., Zhang, H., Shao, D., Wang, M., Wei, Z., Xu, Y., & Wang, J. (2024) | **Score: 8**<br>matched: code review, automated code review, llm, large language model; title/abstract included<br>Sources: openalex |
| 7 | **Improving Automated Code Reviews: Learning From Experience**<br>Lin, H. Y., Thongtanunam, P., Treude, C., & Charoenwet, W. (2024) | **Score: 7**<br>matched: code review, automated code review, large language model; title/abstract included<br>Sources: openalex |
| 8 | **Diggit: Automated code review via software repository mining**<br>Chatley, R., & Jones, L. (2018) | **Score: 6**<br>matched: code review, automated code review; title/abstract included<br>Sources: openalex |
| 9 | **Evaluation of LLM-Based Software Engineering Tools: Practices, Challenges, and Future Directions**<br>Torun, U. B., Karakaya, V., Babar, A., & Tüzün, E. (2026) | **Score: 5**<br>matched: code review, automated code review, llm, large language model, code generation<br>Sources: arxiv |
| 10 | **Towards automating code review at scale**<br>Hellendoorn, V. J., Tsay, J., Mukherjee, M., & Hirzel, M. (2021) | **Score: 5**<br>matched: code review; title/abstract included<br>Sources: openalex |
| 11 | **Automating Code Reviews with Simulink Code Inspector.**<br>Conrad, M., Erkkinen, T., Englehart, M., Lin, X., Nirakh, A. R., Potter, B., Shankar, J., Szpak, P., & Yan, J. (2012) | **Score: 5**<br>matched: code review, automated code review, llm, generated code, code generation<br>Sources: openalex |
| 12 | **AI ASSISTANTS IN SOFTWARE DEVELOPMENT: ANALYSIS OF SECURITY RISKS IN GENERATED CODE**<br>Boichuk, D. (2026) | **Score: 4**<br>matched: code review, llm, large language model, generated code<br>Sources: crossref |
| 13 | **Evaluating LLM-Generated Code: A Benchmark and Developer Study**<br>Szych, J., & Schwerk, A. (2026) | **Score: 4**<br>matched: llm, large language model, generated code, code generation<br>Sources: arxiv |
| 14 | **Fine-Tuning Models for Automated Code Review Feedback**<br>Kumar, S. S., Lones, M. A., Maarek, M., & Zantout, H. (2026) | **Score: 4**<br>matched: code review, automated code review, llm, large language model<br>Sources: arxiv |
| 15 | **From Rocq to Metal: A Pipeline for Formally Verified Microcontroller Firmware**<br>Bergeron, V., & Gorna, K. (2026) | **Score: 4**<br>matched: code review, llm, large language model, generated code<br>Sources: arxiv |
| 16 | **Human-in-the-Loop Governance for LLM-Generated Code:  An Engineering Control, Accountability, and Verification Model  in AI-Augmented Software Development**<br>Taldenko, I. (2026) | **Score: 4**<br>matched: llm, large language model, generated code, code generation<br>Sources: crossref |
| 17 | **Rethinking Code Review in the Age of AI: A Vision for Agentic Code Review**<br>Kamalı, H. s. z. r., Tuna, E., Haratian, V., & Tüzün, E. (2026) | **Score: 4**<br>matched: code review, llm, large language model, code generation<br>Sources: arxiv |
| 18 | **A Review of Research on AI-Assisted Code Generation and AI-Driven Code Review**<br>Wang, Y. (2025) | **Score: 4**<br>matched: code review, llm, large language model, code generation<br>Sources: crossref |
| 19 | **BitsAI-CR: Automated Code Review via LLM in Practice**<br>Sun, T., Xu, J. Q., Li, Y., Yan, Z., Zhang, G., Xie, L., Geng, L., Wang, Z., Chen, Y., Lin, Q., Duan, W., Sui, K., & Zhu, Y. (2025) | **Score: 4**<br>matched: code review, automated code review, llm, large language model<br>Sources: openalex |
| 20 | **Can LLMs Replace Human Evaluators? An Empirical Study of LLM-as-a-Judge in Software Engineering**<br>Wang, R., Guo, J., Gao, C., Fan, G., Chong, C. Y., & Xia, X. (2025) | **Score: 4**<br>matched: llm, large language model, generated code, code generation<br>Sources: openalex |

</details>

The table is limited to the 20 highest-ranked records; the complete metadata remains in the project database and source inventory below.

## Relevant Sources Found Through SLR

This inventory contains the deduplicated records retrieved by the SLR workflow from OpenAlex, Crossref, arXiv, and Semantic Scholar. Entries use APA 7-style author, date, title, source, volume, issue, pages, and DOI/URL formatting when metadata is available. DOI URLs are retained. DOI-bearing records are enriched from Crossref and cached in the local audit database; records without a DOI or unavailable Crossref metadata retain the source fields provided by the original search result. Appearing here does not by itself indicate a final eligibility decision, methodological-quality assessment, or full-text review.

<details>
<summary>Complete source inventory <sub>75 deduplicated records</sub></summary>

<ol>

<li>Aarti, A. (2024). Generative Ai in Software Development : an Overview and Evaluation of Modern Coding Tools. <em>International Journal For Multidisciplinary Research</em>, <em>6</em>(3). <a href="https://doi.org/10.36948/ijfmr.2024.v06i03.23271">https://doi.org/10.36948/ijfmr.2024.v06i03.23271</a></li>
<li>Ahmed, S. (2025). Integrating AI-Driven Automated Code Review in Agile Development: Benefits, Challenges, and Best Practices. <em>International Journal of Advanced Engineering, Management and Science</em>, <em>11</em>(2), 01-10. <a href="https://doi.org/10.22161/ijaems.112.1">https://doi.org/10.22161/ijaems.112.1</a></li>
<li>Alecsandro Bacin, F., Adriano de Mello, B., Dondoni Salton, G., & Da Silva Feitosa, S. (2025). A Systematic Review about Large Language Models (LLMs) applied to Code Generation. <em>Revista Brasileira de Computação Aplicada</em>, <em>17</em>(3), 1-13. <a href="https://doi.org/10.5335/rbca.v17i3.16310">https://doi.org/10.5335/rbca.v17i3.16310</a></li>
<li>Alfonseca, M., & Martín Colino, A. (2026). Using large language models to generate and correct code written in low-resource and domain-specific programming languages. <em>Academia AI and Applications</em>, <em>2</em>(1). <a href="https://doi.org/10.20935/acadai8228">https://doi.org/10.20935/acadai8228</a></li>
<li>Alhashimi, H. A. (2026). A generative AI cybersecurity risks mitigation model for code generation: using ANN-ISM hybrid approach. <em>Scientific Reports</em>, <em>16</em>(1). <a href="https://doi.org/10.1038/s41598-025-34350-3">https://doi.org/10.1038/s41598-025-34350-3</a></li>
<li>Ameen, M. R., Alam, M. T. U., & Islam, A. (2026). QASecClaw: A Multi-Agent LLM Approach for False Positive Reduction in Static Application Security Testing. <em>cs.CR</em>. <a href="https://arxiv.org/pdf/2605.01885v1">https://arxiv.org/pdf/2605.01885v1</a></li>
<li>Asthana, S., Zhang, B., DeLuca, C., Patel, H., & Mahindru, R. (2026). Runtime-Structured Task Decomposition for Agentic Coding Systems. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2605.15425v1">https://arxiv.org/pdf/2605.15425v1</a></li>
<li>Azaad, S. (2026). AI-accelerated meta-analysis in psychology: Large language models code study properties with high accuracy. <em>Behavior Research Methods</em>, <em>58</em>(6). <a href="https://doi.org/10.3758/s13428-026-03020-1">https://doi.org/10.3758/s13428-026-03020-1</a></li>
<li>Bashir, S. (2025). Using pseudo-AI submissions for detecting AI-generated code. <em>Frontiers in Computer Science</em>, <em>7</em>. <a href="https://doi.org/10.3389/fcomp.2025.1549761">https://doi.org/10.3389/fcomp.2025.1549761</a></li>
<li>Bergeron, V., & Gorna, K. (2026). From Rocq to Metal: A Pipeline for Formally Verified Microcontroller Firmware. <em>cs.PL</em>. <a href="https://arxiv.org/pdf/2606.02651v1">https://arxiv.org/pdf/2606.02651v1</a></li>
<li>Bistarelli, S., Fiore, M., Mercanti, I., & Mongiello, M. (2025). Usage of Large Language Model for Code Generation Tasks: A Review. <em>SN Computer Science</em>, <em>6</em>(6). <a href="https://doi.org/10.1007/s42979-025-04241-5">https://doi.org/10.1007/s42979-025-04241-5</a></li>
<li>Boichuk, D. (2026). AI ASSISTANTS IN SOFTWARE DEVELOPMENT: ANALYSIS OF SECURITY RISKS IN GENERATED CODE. <em>Grail of Science</em>(67), 681-687. <a href="https://doi.org/10.36074/grail-of-science.01.05.2026.077">https://doi.org/10.36074/grail-of-science.01.05.2026.077</a></li>
<li>Bulla, L., Midolo, A., Mongiovì, M., & Tramontana, E. (2024). EX-CODE: A Robust and Explainable Model to Detect AI-Generated Code. <em>Information</em>, <em>15</em>(12), 819. <a href="https://doi.org/10.3390/info15120819">https://doi.org/10.3390/info15120819</a></li>
<li>Busch, D., Bainczyk, A., Smyth, S., & Steffen, B. (2025). LLM-based code generation and system migration in language-driven engineering. <em>International Journal on Software Tools for Technology Transfer</em>, <em>27</em>(1), 137-147. <a href="https://doi.org/10.1007/s10009-025-00798-x">https://doi.org/10.1007/s10009-025-00798-x</a></li>
<li>Cai, C., Xiong, B., Wang, C., He, L., & Liang, P. (2026). CoRaCommit: A VS Code Extension for Commit Message Generation with Exemplar Retrieval. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2606.19814v1">https://arxiv.org/pdf/2606.19814v1</a></li>
<li>Chatley, R., & Jones, L. (2018). Diggit: Automated code review via software repository mining. <em>2018 IEEE 25th International Conference on Software Analysis, Evolution and Reengineering (SANER)</em>, 567-571. <a href="https://doi.org/10.1109/saner.2018.8330261">https://doi.org/10.1109/saner.2018.8330261</a></li>
<li>Ciston, S. (2026). Generating the language of AI harms: mapping guardrails using critical code studies. <em>AI &amp; SOCIETY</em>. <a href="https://doi.org/10.1007/s00146-026-02922-0">https://doi.org/10.1007/s00146-026-02922-0</a></li>
<li>Conrad, M., Erkkinen, T., Englehart, M., Lin, X., Nirakh, A. R., Potter, B., Shankar, J., Szpak, P., & Yan, J. (2012). Automating Code Reviews with Simulink Code Inspector.. <em>MBEES</em>. <a href="https://www.mathworks.com/tagteam/71296_CEE+15.pdf">https://www.mathworks.com/tagteam/71296_CEE+15.pdf</a></li>
<li>Cynthia, S. T., Widyasari, R., Roy, B., Zhang, T., & Lo, D. (2026). "Go Home Copilot, You're Drunk": Understanding Developer Responses to Agent-Generated Code Review Comments. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2607.21997v2">https://arxiv.org/pdf/2607.21997v2</a></li>
<li>Deng, J., Fan, Z., & Meng, R. (2026). Understanding the (In)Security of Vibe-Coded Applications. <em>cs.CR</em>. <a href="https://arxiv.org/pdf/2606.23130v2">https://arxiv.org/pdf/2606.23130v2</a></li>
<li>Dhruvitkumar V. Talati (2025). AI-Generated code for cloud devOps: Automating infrastructure as code. <em>International Journal of Science and Research Archive</em>, <em>14</em>(3), 339-345. <a href="https://doi.org/10.30574/ijsra.2025.14.3.0608">https://doi.org/10.30574/ijsra.2025.14.3.0608</a></li>
<li>Diaconescu, A. I. (2013). Automated Code Review for Fault Injection. <em>Research Repository (Delft University of Technology)</em>. <a href="http://resolver.tudelft.nl/uuid:38e13168-0a82-48da-a598-3b8cb3c027e4">http://resolver.tudelft.nl/uuid:38e13168-0a82-48da-a598-3b8cb3c027e4</a></li>
<li>Ding, Y., & Shao, J. (2026). GPU and CPU Memory Co-Optimization in Heterogeneous Pipeline Parallelism for Efficient Large Language Model Fine-Tuning on Commodity Servers. <em>ACM Transactions on Architecture and Code Optimization</em>. <a href="https://doi.org/10.1145/3839239">https://doi.org/10.1145/3839239</a></li>
<li>Dolcetti, G., & Iotti, E. (2025). A dual perspective review on large language models and code verification. <em>Frontiers in Computer Science</em>, <em>7</em>. <a href="https://doi.org/10.3389/fcomp.2025.1655469">https://doi.org/10.3389/fcomp.2025.1655469</a></li>
<li>Fendley, N., Liu, Z., Guan, A., Zhong, J., & Cao, Y. (2026). Comment and Control: Hijacking Agentic Workflows via Context-Grounded Evolution. <em>cs.CR</em>. <a href="https://arxiv.org/pdf/2605.11229v1">https://arxiv.org/pdf/2605.11229v1</a></li>
<li>Fowles, P., Falor, E., Bhattarai, S., Edwards, J., & Poulsen, S. (2026). Combating Harms of Generative AI in CS1 with Code Review Interviews and a Flipped Classroom. <em>cs.HC</em>. <a href="https://arxiv.org/pdf/2605.21374v1">https://arxiv.org/pdf/2605.21374v1</a></li>
<li>Gao, Z., Barón, M. M. o., Habiba, U. e., Graziotin, D., & Wagner, S. (2026). Evaluating the Impact of Explainable AI on Trust in AI-Assisted Code Review. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2607.24601v1">https://arxiv.org/pdf/2607.24601v1</a></li>
<li>Gupta, M., Akiri, C., Aryal, K., Parker, E., & Praharaj, L. (2023). From ChatGPT to ThreatGPT: Impact of Generative AI in Cybersecurity and Privacy. <em>IEEE Access</em>, <em>11</em>, 80218-80245. <a href="https://doi.org/10.1109/access.2023.3300381">https://doi.org/10.1109/access.2023.3300381</a></li>
<li>Hellendoorn, V. J., Tsay, J., Mukherjee, M., & Hirzel, M. (2021). Towards automating code review at scale. <em>Proceedings of the 29th ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software Engineering</em>, 1479-1482. <a href="https://doi.org/10.1145/3468264.3473134">https://doi.org/10.1145/3468264.3473134</a></li>
<li>Jiang, R., Xia, K., Huang, J., & Lu, J. (2026). Large Language Model-Based Method for HVAC System Control Code Automatic Generation. <em>Buildings</em>, <em>16</em>(9), 1722. <a href="https://doi.org/10.3390/buildings16091722">https://doi.org/10.3390/buildings16091722</a></li>
<li>Kamalı, H. s. z. r., Tuna, E., Haratian, V., & Tüzün, E. (2026). Rethinking Code Review in the Age of AI: A Vision for Agentic Code Review. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2605.17548v2">https://arxiv.org/pdf/2605.17548v2</a></li>
<li>Kharel, P. S., & Thapalia, S. (2026). Assessing the Impact of Ai Vibe Coding on Reviewing and Debugging Ai-generated Code. <em>International Journal For Multidisciplinary Research</em>, <em>8</em>(4). <a href="https://doi.org/10.36948/ijfmr.2026.v08i04.85314">https://doi.org/10.36948/ijfmr.2026.v08i04.85314</a></li>
<li>Khojah, R., Neto, F. G. d. O., Mohamad, M., Frattini, J., & Leitner, P. (2026). Same Scrutiny, More Time: Eye Tracking Insights into Reviewing LLM-Labelled Code. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2606.26505v1">https://arxiv.org/pdf/2606.26505v1</a></li>
<li>Kumar, S. S., Lones, M. A., Maarek, M., & Zantout, H. (2026). Fine-Tuning Models for Automated Code Review Feedback. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2605.12610v1">https://arxiv.org/pdf/2605.12610v1</a></li>
<li>Li, Z., Lu, S., Guo, D., Duan, Jannu, S., Jenks, G., Majumder, D., Green, J., Svyatkovskiy, A., Fu, S., & Sundaresan, N. (2022). Automating Code Review Activities by Large-Scale Pre-training. <em>arXiv (Cornell University)</em>. <a href="https://doi.org/10.48550/arxiv.2203.09095">https://doi.org/10.48550/arxiv.2203.09095</a></li>
<li>Li, K., Zhu, A., Zhou, W., Zhao, P., Song, J., & Liu, J. (2024). Utilizing Deep Learning to Optimize Software Development Processes. <em>arXiv (Cornell University)</em>. <a href="https://doi.org/10.48550/arxiv.2404.13630">https://doi.org/10.48550/arxiv.2404.13630</a></li>
<li>Li, M., Qiu, M., Peng, Z., Fan, H., Fu, S., Ding, J., & Feng, Y. (2026). Beyond Refusal: A Same-Lineage Study of Aligned and Abliterated LLMs for Vulnerability Analysis. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2607.05842v1">https://arxiv.org/pdf/2607.05842v1</a></li>
<li>Lin, H. Y., Thongtanunam, P., Treude, C., & Charoenwet, W. (2024). Improving Automated Code Reviews: Learning From Experience. <em>Proceedings of the 21st International Conference on Mining Software Repositories</em>, 278-283. <a href="https://doi.org/10.1145/3643991.3644910">https://doi.org/10.1145/3643991.3644910</a></li>
<li>Liu, Z., Ruinan, Z., Wang, D., Peng, G. D., Wang, J., Liu, Q., Liu, P., & Wang, W. (2024). Agents4PLC: Automating Closed-loop PLC Code Generation and Verification in Industrial Control Systems using LLM-based Agents. <em>arXiv (Cornell University)</em>. <a href="https://doi.org/10.48550/arxiv.2410.14209">https://doi.org/10.48550/arxiv.2410.14209</a></li>
<li>Liu, Y., Tantithamthavorn, C., Liu, Y., & Li, L. (2024). On the Reliability and Explainability of Language Models for Program Generation. <em>ACM Transactions on Software Engineering and Methodology</em>, <em>33</em>(5), 1-26. <a href="https://doi.org/10.1145/3641540">https://doi.org/10.1145/3641540</a></li>
<li>Marino, M. C., & Douglass, J. (2026). Critical Code Sudies with AI: conversing with LLMs about code. <em>AI &amp; SOCIETY</em>. <a href="https://doi.org/10.1007/s00146-026-02958-2">https://doi.org/10.1007/s00146-026-02958-2</a></li>
<li>Melo, R., Fogliato, R., Zhou, S., Thaker, P., & Wu, Z. S. (2026). SEVRA-BENCH: Social Engineering of Vulnerabilities in Review Agents. <em>cs.CR</em>. <a href="https://arxiv.org/pdf/2606.13757v2">https://arxiv.org/pdf/2606.13757v2</a></li>
<li>Monperrus, M. (2026). The End of Code Review: Coding Agents Supersede Human Inspection. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2606.13175v1">https://arxiv.org/pdf/2606.13175v1</a></li>
<li>Ochodek, M. a., & Staron, M. (2024). ACoRA – A Platform for Automating Code Review Tasks. <em>e-Informatica Software Engineering Journal</em>, <em>19</em>(1), 250102. <a href="https://doi.org/10.37190/e-inf250102">https://doi.org/10.37190/e-inf250102</a></li>
<li>Paltenghi, M., & Chandra, S. (2026). AfterVibe: What Remains When the Conversation Ends. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2607.09900v1">https://arxiv.org/pdf/2607.09900v1</a></li>
<li>Pinna, G., Ravalico, D., Rovito, L., Manzoni, L., & De Lorenzo, A. (2025). Exploring the Effect of Genetic Improvement for Large Language Models-Generated Code. <em>SN Computer Science</em>, <em>6</em>(7). <a href="https://doi.org/10.1007/s42979-025-04281-x">https://doi.org/10.1007/s42979-025-04281-x</a></li>
<li>Punithavel, R. K., & Deeksha Sivakumer (2025). Large Language Model Framework for Device Orchestration in Low-Code No-Code Solutions. <em>International Journal of Computational and Experimental Science and Engineering</em>, <em>11</em>(3). <a href="https://doi.org/10.22399/ijcesen.3521">https://doi.org/10.22399/ijcesen.3521</a></li>
<li>Qi, X., Fang, J., Zhang, P., & Che, Y. (2026). Optimizing Attention for Large Language Model Inference on the MT-3000 Many-Core Processor. <em>ACM Transactions on Architecture and Code Optimization</em>, <em>23</em>(2), 1-27. <a href="https://doi.org/10.1145/3807449">https://doi.org/10.1145/3807449</a></li>
<li>Rahman, M., Khatoonabadi, S., Abdellatif, A., & Shihab, E. (2024). Automatic Detection of LLM-Generated Code: A Comparative Case Study of Contemporary Models Across Function and Class Granularities. <em>arXiv (Cornell University)</em>. <a href="https://doi.org/10.48550/arxiv.2409.01382">https://doi.org/10.48550/arxiv.2409.01382</a></li>
<li>Sghaier, O. B., Weyssow, M., & Sahraoui, H. (2026). Balancing Usefulness and Naturalness: An LLM-based Curation Pipeline for Code Review Comments. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2607.09524v1">https://arxiv.org/pdf/2607.09524v1</a></li>
<li>Sharma, I., & Rattan, D. (2025). Code Quality Generated by AI Tools: A Review. <em>IOSR Journal of Computer Engineering</em>, <em>27</em>(3), 55-68. <a href="https://doi.org/10.9790/0661-2703035568">https://doi.org/10.9790/0661-2703035568</a></li>
<li>Song, X., Cai, Z., & Zhao, L. (2026). When AI Reviews Its Own Code: Recursive Self-Training Collapse in Code LLMs. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2606.28438v1">https://arxiv.org/pdf/2606.28438v1</a></li>
<li>Sun, T., Xu, J. Q., Li, Y., Yan, Z., Zhang, G., Xie, L., Geng, L., Wang, Z., Chen, Y., Lin, Q., Duan, W., Sui, K., & Zhu, Y. (2025). BitsAI-CR: Automated Code Review via LLM in Practice. <em>Proceedings of the 33rd ACM International Conference on the Foundations of Software Engineering</em>, 274-285. <a href="https://doi.org/10.1145/3696630.3728552">https://doi.org/10.1145/3696630.3728552</a></li>
<li>Szych, J., & Schwerk, A. (2026). Evaluating LLM-Generated Code: A Benchmark and Developer Study. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2605.09059v2">https://arxiv.org/pdf/2605.09059v2</a></li>
<li>Taldenko, I. (2026). Human-in-the-Loop Governance for LLM-Generated Code:  An Engineering Control, Accountability, and Verification Model  in AI-Augmented Software Development. <em>EJSMT</em>, <em>2</em>(3), 140-149. <a href="https://doi.org/10.59324/ejsmt.2026.2(3).12">https://doi.org/10.59324/ejsmt.2026.2(3).12</a></li>
<li>Torun, U. B., Karakaya, V., Babar, A., & Tüzün, E. (2026). Evaluation of LLM-Based Software Engineering Tools: Practices, Challenges, and Future Directions. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2604.24621v1">https://arxiv.org/pdf/2604.24621v1</a></li>
<li>Tufano, R., Pascarella, L., Tufano, M., Poshyvanyk, D., & Bavota, G. (2021). Towards Automating Code Review Activities. <em>2021 IEEE/ACM 43rd International Conference on Software Engineering (ICSE)</em>, 163-174. <a href="https://doi.org/10.1109/icse43902.2021.00027">https://doi.org/10.1109/icse43902.2021.00027</a></li>
<li>Veeramreddygari, U. K. R. (2023). Generative AI for Software Engineering: Large Language Model-Driven Code Generation with Safety and Trust Assessment in Enterprise Development. <em>International Journal of Scientific Research in Computer Science, Engineering and Information Technology</em>, 569-582. <a href="https://doi.org/10.32628/cseit23906195">https://doi.org/10.32628/cseit23906195</a></li>
<li>Wang, S., Geng, M., Lin, B., Sun, Z., Wen, M., Liu, Y., Li, L., Bissyandé, T. F., & Mao, X. (2023). Natural Language to Code: How Far Are We?. <em>Proceedings of the 31st ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering</em>, 375-387. <a href="https://doi.org/10.1145/3611643.3616323">https://doi.org/10.1145/3611643.3616323</a></li>
<li>Wang, Y. (2025). A Review of Research on AI-Assisted Code Generation and AI-Driven Code Review. <em>Academic Journal of Science and Technology</em>, <em>18</em>(2), 236-241. <a href="https://doi.org/10.54097/d6775287">https://doi.org/10.54097/d6775287</a></li>
<li>Wang, R., Guo, J., Gao, C., Fan, G., Chong, C. Y., & Xia, X. (2025). Can LLMs Replace Human Evaluators? An Empirical Study of LLM-as-a-Judge in Software Engineering. <em>Proceedings of the ACM on Software Engineering</em>, <em>2</em>(ISSTA), 1955-1977. <a href="https://doi.org/10.1145/3728963">https://doi.org/10.1145/3728963</a></li>
<li>Wei, K. (2026). A Method for Alleviating Illusions in Code Generation Based on a Large Language Model Generated by Retrieval Enhancement. <em>Advanced Electromagnetics</em>, <em>15</em>(3), 8519-8525. <a href="https://doi.org/10.7716/aem.v15i3.3976">https://doi.org/10.7716/aem.v15i3.3976</a></li>
<li>Weiss, B., Abu-Nassar, A., Sosnovich, A., & Yorav, K. (2026). Beyond Summaries: Structure-Aware Labeling of Code Changes with Large Language Models. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2605.26100v1">https://arxiv.org/pdf/2605.26100v1</a></li>
<li>Weyssow, M., Zhou, X., Kim, K., Lo, D., & Sahraoui, H. (2023). Exploring Parameter-Efficient Fine-Tuning Techniques for Code Generation with Large Language Models. <em>arXiv (Cornell University)</em>. <a href="https://doi.org/10.48550/arxiv.2308.10462">https://doi.org/10.48550/arxiv.2308.10462</a></li>
<li>Wong, M. F., Guo, S., Hang, C. N., Ho, S. W., & Tan, C. W. (2023). Natural Language Generation and Understanding of Big Code for AI-Assisted Programming: A Review. <em>Entropy</em>, <em>25</em>(6), 888. <a href="https://doi.org/10.3390/e25060888">https://doi.org/10.3390/e25060888</a></li>
<li>Wu, Z., & Nita-Rotaru, C. (2026). ALIBI: Adaptive Agentic Attacks on LLM-Based Vulnerability Detectors via Adversarial Code Comments. <em>cs.CR</em>. <a href="https://arxiv.org/pdf/2607.24964v1">https://arxiv.org/pdf/2607.24964v1</a></li>
<li>Xiong, B., Cai, C., Xiong, K., Wang, C., & Liang, P. (2026). Assessing Language Models for Salient Class Identification. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2606.21629v1">https://arxiv.org/pdf/2606.21629v1</a></li>
<li>Xu, Z., & Sheng, V. S. (2024). Detecting AI-Generated Code Assignments Using Perplexity of Large Language Models. <em>Proceedings of the AAAI Conference on Artificial Intelligence</em>, <em>38</em>(21), 23155-23162. <a href="https://doi.org/10.1609/aaai.v38i21.30361">https://doi.org/10.1609/aaai.v38i21.30361</a></li>
<li>Yang, Y. (2023). Improving Code Completion by Solving Data Inconsistencies in the Source Code with a Hierarchical Language Model. <em>Electronics</em>, <em>12</em>(7), 1576. <a href="https://doi.org/10.3390/electronics12071576">https://doi.org/10.3390/electronics12071576</a></li>
<li>Yin, Y., Zhao, Y., Sun, Y., & Chen, C. (2023). Automatic Code Review by Learning the Structure Information of Code Graph. <em>Sensors</em>, <em>23</em>(5), 2551. <a href="https://doi.org/10.3390/s23052551">https://doi.org/10.3390/s23052551</a></li>
<li>Yu, Y., Rong, G., Shen, H., Zhang, H., Shao, D., Wang, M., Wei, Z., Xu, Y., & Wang, J. (2024). Fine-Tuning Large Language Models to Improve Accuracy and Comprehensibility of Automated Code Review. <em>ACM Transactions on Software Engineering and Methodology</em>, <em>34</em>(1), 1-26. <a href="https://doi.org/10.1145/3695993">https://doi.org/10.1145/3695993</a></li>
<li>Zhang, J., Panthaplackel, S., Nie, P., Li, J. J., & Gligoric, M. (2022). CoditT5: Pretraining for Source Code and Natural Language Editing. <em>Proceedings of the 37th IEEE/ACM International Conference on Automated Software Engineering</em>, 1-12. <a href="https://doi.org/10.1145/3551349.3556955">https://doi.org/10.1145/3551349.3556955</a></li>
<li>Zhang, Z., & Saber, T. (2025). Exploring the Boundaries Between LLM Code Clone Detection and Code Similarity Assessment on Human and AI-Generated Code. <em>Big Data and Cognitive Computing</em>, <em>9</em>(2), 41. <a href="https://doi.org/10.3390/bdcc9020041">https://doi.org/10.3390/bdcc9020041</a></li>
<li>Zhong, S., Noei, S., Adams, B., & Zou, Y. (2026). From Human-Centric to Agentic Code Review: The Impact of Different Generations of Generative AI Technology on Review Quality. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2607.13196v1">https://arxiv.org/pdf/2607.13196v1</a></li>
<li>Çağlar, S., Gökırmak, k. E., & Tüzün, E. (2026). Automated Classification of Human Code Review Comments with Large Language Models. <em>cs.SE</em>. <a href="https://arxiv.org/pdf/2604.23667v1">https://arxiv.org/pdf/2604.23667v1</a></li>
</ol>

</details>

## Reproducibility Notes

<details>
<summary>Audit-retention notes <sub>publication checklist</sub></summary>

- The project directory and SQLite audit database retain queries, source hits, deduplication, screening decisions, download attempts, and local PDF paths.
- SURF AI-HUB advice is runtime-selected and displayed without writing a decision; record the selected model and request scope before publication.
- Review results, especially metadata-only records and screening decisions, before publication.

</details>

### Jupyter Kernel Transport Security

<details>
<summary>Local and remote kernel controls <sub>security note</sub></summary>

The warning means ZeroMQ traffic between the notebook interface and kernel is not transport-encrypted. For local Windows use, it is informational when VS Code and the kernel run on the same machine through `127.0.0.1`; do not expose that traffic to a network. IPC is not the dependable Windows alternative.

Keep `jupyter_client`, `ipykernel`, and `pyzmq` current in `prisma-env`; keep secrets out of cells and outputs; and store them only in the uncommitted local `.env`. For a remote kernel, use VS Code Remote SSH or an SSH tunnel with Jupyter bound to `127.0.0.1`. Organization-managed or network-accessible kernels should use administrator-provisioned CurveZMQ encryption.

</details>

## Appendix A. Verantwoording en correcties

<details>
<summary>Transparency, legal, and ethical qualifications <sub>supporting material</sub></summary>

Deze rapportage is opgesteld met ondersteuning van generatieve AI. De auteur blijft verantwoordelijk voor de onderzoeksopzet, de controle van de feiten, de selectie van bronnen, de inhoudelijke interpretatie en de uiteindelijke tekst. AI-uitvoer is gebruikt als ondersteuning en niet als zelfstandig bewijs of als vervanging van menselijk oordeel.

### Gebruikte AI-ondersteuning

| Tool of component | Rol in deze rapportage | Beheersmaatregel |
| --- | --- | --- |
| SURF AI-HUB Qwen 2.5 Instruct model (minimaal 32B) | Begrensd advies bij screening van een kandidaatrecord. | Model is runtime geselecteerd; advies schrijft geen beslissing en vereist menselijke beoordeling. |
| SLR-Engine workflow | Herleidbare zoek-, deduplicatie-, screening- en exportstappen. | Queries, bronhits, beslissingen en downloaduitkomsten blijven lokaal auditbaar. |

### Juridische en ethische uitgangspunten

- **Artikel 5 AVG:** doelbinding en dataminimalisatie zijn relevant voor zover in de workflow persoonsgegevens worden verwerkt.
- **Artikel 12 AVG:** informatie over verwerking van persoonsgegevens moet duidelijk en toegankelijk zijn wanneer betrokkenen moeten worden geinformeerd.
- **Artikel 13 AI Act:** bevat transparantieverplichtingen voor hoog-risico-AI-systemen; de bepaling is alleen van toepassing wanneer een systeem onder die categorie valt.
- **Artikel 50 AI Act:** bevat specifieke transparantieverplichtingen, onder meer rond AI-interactie en bepaalde synthetische inhoud. De toepasselijkheid hangt af van de concrete inzet en rol van het AI-systeem.

Deze appendix is een transparantieverklaring voor deze rapportage en geen juridisch advies. Bij verwerking van persoonsgegevens of inzet in een gereguleerde context is aanvullende toetsing nodig.

</details>

## Appendix B. Reproducible Procedure and Code-Cell Explanation

<details>
<summary>Local reproduction procedure and verbatim notebook code <sub>technical appendix</sub></summary>

This appendix documents the executable V04 workflow. It enables local reproduction without treating AI output as a final scholarly decision.

### Copy the SLR Workflow Locally on Windows 11

Reproduction requires the complete local SLR-Engine repository; this report alone lacks its `scripts/`, `slr_engine/`, tests, query files, and project database.

1. Install [Git for Windows](https://git-scm.com/download/win) and Anaconda or Miniconda if they are not already installed.
2. Open **PowerShell** and choose a local working folder, for example Documents:

```powershell
Set-Location $HOME\Documents
git clone https://github.com/tuirk/SLR-Engine.git
Set-Location .\SLR-Engine
```

3. To reproduce this evidence state, copy `projects\Willma_SLR` into the clone's `projects` folder, for example `C:\Users\<your-user-name>\Documents\SLR-Engine\projects\Willma_SLR`.
4. Open the repository with `code .`, then open `SLR_Engine_V04_SURF_AI_HUB_Demo.ipynb` after completing the prerequisites.

### Prerequisites

1. Open `SLR_Engine_V04_SURF_AI_HUB_Demo.ipynb` from the SLR-Engine repository root.
2. Select the `prisma-env` Jupyter kernel and install the repository dependencies in that environment.
3. Create a repository-root `.env` file containing `SURF_AI_HUB_API_KEY=<key>`. Optionally set `SURF_AI_HUB_MODEL=<visible eligible model name>` to pin a model; otherwise the notebook selects the largest eligible model.
4. Allow outbound HTTPS access to OpenAlex, Crossref, arXiv, Semantic Scholar, `https://api.willma.surf.nl`, and `https://willma.surf.nl`. Results and visible models vary by date, network, API key, and source availability.
5. Run cells in order. Do not rerun deduplication after screening decisions exist; the notebook reuses existing batches.

### Code Cells and Their Exact Role

1. [**Kernel verification.**](#code-cell-1) Prints the executable, Python version, and environment prefix, then raises an error unless the active interpreter belongs to `prisma-env`. This prevents a notebook from silently running in the base Conda environment.
2. [**Repository verification.**](#code-cell-2) Confirms `README.md`, `scripts/`, `slr_engine/`, and `tests/` exist below the current working directory, then runs `pytest -q` with the active interpreter. It stops on test failure before project data is changed.
3. [**Project and protocol initialization.**](#code-cell-3) Creates or reuses `projects/Willma_SLR`, then writes `project.yaml` with the topic, aim, research questions, inclusion criteria I1-I3, exclusion criteria E1-E3, seed placeholders, and `agent` as the advisory provider.
4. [**Protocol display.**](#code-cell-4) Renders the saved protocol as a pandas table. It is a review checkpoint: verify the research question and eligibility criteria before any retrieval.
5. [**Bounded literature search.**](#code-cell-5) Writes literal query files under `projects/Willma_SLR/queries/`, calls `scripts/02_search_open.py` for OpenAlex, Crossref, arXiv, and Semantic Scholar with a 25-record-per-source cap, then queries `project.db` to display the first ten provenance-backed records.
6. [**Retrieved-evidence inspection.**](#code-cell-6) Reads all database records and source hits, calculates a transparent count of topic-term signals, and displays per-source, per-year, and per-paper tables. This score only prioritizes inspection; it is not a screening decision.
7. [**PDF resources map.**](#code-cell-7) Reads successful PDF downloads, validates the `%PDF-` signature, hard-links or copies each valid file to `projects/Willma_SLR/resources/pdfs/`, and writes CSV and Markdown manifests with source and resolver provenance.
8. [**SURF AI-HUB advisory call.**](#code-cell-8) Reuses an existing unreviewed screening batch or runs `03_dedup.py` and `04_screen_prep.py`. It sends one candidate title and abstract to SURF AI-HUB, discovers models through `/v0/sequences`, requires a text Qwen 2.5 Instruct model with at least 32B parameters, and posts a bounded advisory prompt to `/api/v0/chat/completions`. The notebook then displays `recommendation_table` with the candidate title, selected model, full advisory text, and human-decision requirement, followed by a token-usage table. These are display outputs only: the cell does not write the advisory to `project.db` or a screening JSONL file, and it does not write a screening decision.
9. [**First reviewed batch and downloads.**](#code-cell-9) Writes demo labels for `batch_001.jsonl`, commits them with `04b_screen_commit.py`, resolves lawful open-access locations with `05_resolve_oa.py`, and downloads with `06_download.py`. Replace the example labels and reasons with independently reviewed judgements before using this as a study dataset. The `--decided-by agent` value is provenance metadata, not evidence that an AI may make final decisions.
10. [**Additional reviewed batch.**](#code-cell-10) Selects the five hard-coded database record IDs 52, 53, 54, 58, and 59, writes `batch_002.jsonl`, commits the supplied include labels, then retries OA resolution and downloads. These IDs are specific to the saved demo database and must be replaced by stable canonical identifiers or a human-selected query in a fresh reproduction.
11. [**Evidence report export.**](#code-cell-11) Reads the SQLite audit tables and query files, calculates the report ranking, creates an HTML-compatible APA-style reference list from available metadata, and writes `projects/Willma_SLR/ai_written_code_review.md`. Its ranking is exactly: matched topic-term count + 4 for a committed include decision + 2 for a verified downloaded PDF.
12. [**Compact ranking refresh.**](#code-cell-12) Replaces only the generated report ranking section using the in-memory ranked records. It is a formatting refresh and must be run after the report-export cell in the same kernel.
13. [**Standalone APA-style export.**](#code-cell-13) Reads `project.db` independently and writes `projects/Willma_SLR/references_apa.md`. It preserves source-limited first-author metadata and must not be interpreted as a fully verified APA bibliography.
### AI and SLR Decision Boundary
- The AI service receives one selected candidate title and abstract, not repository source code and not an entire screening batch.
- The model prompt requires `Decision`, `Reason`, `Criteria`, and `Human review required: yes`; its response is displayed but never inserted into the `screening` table by the advisory cell.
- SLR inclusion and exclusion decisions must be reviewed against I1-I3 and E1-E3, documented with reasons, and retained in `project.db` and JSONL batch files.
- Downloading is limited to resolver-discovered open-access copies; failed or blocked downloads remain audit outcomes and must not be bypassed.
- Reproducibility means preserving the notebook version, package versions, literal query files, source timestamps, project database, batch JSONL files, model name, prompt, raw response, and human-decision provenance. It does not mean that a future source search or model call will return identical results.
### Expected Outputs
- `projects/Willma_SLR/project.yaml`: protocol and configuration.
- `projects/Willma_SLR/project.db`: records, source hits, screening, and download audit trail.
- `projects/Willma_SLR/queries/`: literal source queries.
- `projects/Willma_SLR/screening/`: prepared and reviewed JSONL batches.
- `projects/Willma_SLR/resources/`: verified PDF map and manifests when lawful PDFs are available.
- `projects/Willma_SLR/ai_written_code_review.md` and `references_apa.md`: human-readable evidence and source-metadata exports.
### Verbatim Code by Cell

The following blocks are copied directly from the notebook source at report-generation time. They contain no secret values; API keys are read from `.env` at runtime.

#### Code Cell 1

```python
from pathlib import Path
import platform
import sys

expected_kernel = 'prisma-env'
python_path = Path(sys.executable)
kernel_description = {
    'Python executable': str(python_path),
    'Python version': platform.python_version(),
    'Environment prefix': sys.prefix,
}

for label, value in kernel_description.items():
    print(f'{label}: {value}')

if expected_kernel not in str(python_path).lower() and expected_kernel not in sys.prefix.lower():
    raise RuntimeError(
        'Wrong kernel loaded. Select the prisma-env kernel, then restart and run this notebook again.'
    )

print(f'Kernel check passed: {expected_kernel}')
```

#### Code Cell 2

```python
import subprocess

repo_root = Path.cwd().resolve()
required_paths = [
    repo_root / 'README.md',
    repo_root / 'scripts' / '00_init_project.py',
    repo_root / 'slr_engine',
    repo_root / 'tests',
]
missing_paths = [str(path) for path in required_paths if not path.exists()]
if missing_paths:
    raise FileNotFoundError(
        'Open this notebook from the SLR-Engine repository root. Missing: ' + ', '.join(missing_paths)
    )

test_result = subprocess.run(
    [sys.executable, '-m', 'pytest', '-q'],
    cwd=repo_root,
    text=True,
    capture_output=True,
)
print(test_result.stdout)
if test_result.returncode:
    print(test_result.stderr)
    raise RuntimeError(f'Repository tests failed with exit code {test_result.returncode}.')

print('Repository test suite passed.')
```

#### Code Cell 3

```python
from slr_engine.store import ProjectConfig, init_project

project_id = 'Willma_SLR'
project_root = repo_root / 'projects' / project_id
topic = 'The Problem With Using AI to Review AI-Written Code'

if not project_root.exists():
    init_project(repo_root / 'projects', project_id, topic=topic)
    print(f'Created project: {project_root}')
else:
    print(f'Reusing existing project: {project_root}')

config = ProjectConfig.load(project_root)
config.topic = topic
config.aim = (
    'Synthesize empirical evidence about the reliability, risks, and human oversight '
    'needed when AI reviews AI-written code.'
)
config.research_questions = [
    'What evidence evaluates AI review of AI-written code?',
    'Which defects, risks, and failure modes are missed or introduced?',
    'Which human oversight and reproducibility practices are reported?',
]
config.inclusion = [
    {'id': 'I1', 'text': 'Empirical study, benchmark, or systematic evaluation.'},
    {'id': 'I2', 'text': 'Evaluates AI-assisted or AI-driven code review, code analysis, or defect detection.'},
    {'id': 'I3', 'text': 'Reports methods, data, outcomes, or documented limitations.'},
]
config.exclusion = [
    {'id': 'E1', 'text': 'Opinion-only content without a described evaluation method.'},
    {'id': 'E2', 'text': 'General code generation without a review or evaluation component.'},
    {'id': 'E3', 'text': 'Duplicate publication or insufficient bibliographic metadata.'},
]
config.seed_examples = {
    'include': ['Replace with verified seed papers after human review.'],
    'exclude': ['Marketing claims about AI code review without an evaluation.'],
}
config.llm = {'provider': 'agent'}
config.save(project_root)

print(f'Protocol saved: {project_root / "project.yaml"}')
```

#### Code Cell 4

```python
import pandas as pd

protocol_rows = [
    ('Topic', config.topic),
    ('Aim', config.aim),
    ('Research questions', '\n'.join(config.research_questions)),
    ('Inclusion criteria', '\n'.join(item['id'] + ': ' + item['text'] for item in config.inclusion)),
    ('Exclusion criteria', '\n'.join(item['id'] + ': ' + item['text'] for item in config.exclusion)),
    ('Decision provider', config.judgment_provider()),
]
protocol_table = pd.DataFrame(protocol_rows, columns=['Protocol item', 'Value'])
pd.set_option('display.max_colwidth', 1_000)
display(protocol_table)
```

#### Code Cell 5

```python
import json
import sqlite3

query_texts = {
    'concepts.yaml': """concepts:
  - id: C1
    preferred: AI-assisted code review
    synonyms:
      - AI code review
      - LLM code review
      - automated code review
  - id: C2
    preferred: AI-generated code
    synonyms:
      - generated code
      - code generation
      - large language model code
""",
    'openalex.txt': (
        '("AI code review" OR "LLM code review" OR "automated code review") '
        'AND ("AI-generated code" OR "generated code" OR "code generation")'
    ),
    'arxiv.txt': (
        '(all:"code review" OR all:"automated code review") '
        'AND (all:"large language model" OR all:"AI generated code")'
    ),
    'semantic_scholar.txt': (
        '("AI code review" OR "LLM code review") '
        'AND ("AI-generated code" OR "code generation")'
    ),
    'crossref.json': json.dumps(
        {
            'filter': {'type': 'journal-article', 'has-abstract': 'true'},
            'query.bibliographic': [
                'AI code review',
                'large language model generated code',
            ],
        },
        indent=2,
    ),
}

for filename, content in query_texts.items():
    (project_root / 'queries' / filename).write_text(content + '\n', encoding='utf-8')

search_result = subprocess.run(
    [
        sys.executable,
        'scripts/02_search_open.py',
        '--project',
        project_id,
        '--sources',
        'openalex,crossref,arxiv,semantic_scholar',
        '--max-records',
        '25',
        '--acknowledge-warnings',
    ],
    cwd=repo_root,
    text=True,
    capture_output=True,
 )
print(search_result.stdout)
if search_result.returncode:
    print(search_result.stderr)
    raise RuntimeError(f'External literature search failed with exit code {search_result.returncode}.')

with sqlite3.connect(project_root / 'project.db') as connection:
    evidence_table = pd.read_sql_query(
        """
        SELECT
            records.title,
            records.year,
            records.first_author,
            records.venue,
            records.abstract,
            GROUP_CONCAT(DISTINCT source_hits.source) AS sources
        FROM records
        LEFT JOIN source_hits ON source_hits.record_id = records.id
        GROUP BY records.id
        ORDER BY records.id
        LIMIT 10
        """,
        connection,
    )

if evidence_table.empty:
    raise RuntimeError('The search completed but returned no records to review.')

display(evidence_table)
```

#### Code Cell 6

```python
# Human-readable overview of the retrieved evidence before screening.
with sqlite3.connect(project_root / 'project.db') as connection:
    papers = pd.read_sql_query(
        """
        SELECT
            records.canonical_id,
            records.title,
            records.year,
            records.first_author,
            records.venue,
            records.abstract,
            records.url,
            GROUP_CONCAT(DISTINCT source_hits.source) AS sources
        FROM records
        LEFT JOIN source_hits ON source_hits.record_id = records.id
        GROUP BY records.id
        """,
        connection,
    )

relevance_terms = (
    'code review',
    'automated code review',
    'ai code review',
    'llm',
    'large language model',
    'generated code',
    'code generation',
    'llm-as-a-judge',
 )

def relevance_score(paper):
    text = f"{paper['title'] or ''} {paper['abstract'] or ''}".lower()
    return sum(term in text for term in relevance_terms)

papers['relevance_signals'] = papers.apply(relevance_score, axis=1)
papers['abstract_preview'] = papers['abstract'].fillna('').str.replace(r'\s+', ' ', regex=True).str.slice(0, 350)
papers.loc[papers['abstract_preview'].str.len() == 350, 'abstract_preview'] += '...'

paper_overview = (
    papers.sort_values(['relevance_signals', 'year', 'title'], ascending=[False, False, True])
    .loc[:, [
        'canonical_id',
        'title',
        'year',
        'first_author',
        'venue',
        'sources',
        'relevance_signals',
        'abstract_preview',
        'url',
    ]]
    .reset_index(drop=True)
 )

source_overview = (
    papers.assign(source=papers['sources'].fillna('unknown').str.split(','))
    .explode('source')
    .groupby('source', dropna=False)['canonical_id']
    .nunique()
    .rename('papers')
    .reset_index()
    .sort_values('papers', ascending=False)
 )

year_overview = (
    papers.groupby('year', dropna=False)['canonical_id']
    .nunique()
    .rename('papers')
    .reset_index()
    .sort_values('year', ascending=False)
 )

print(f'Retrieved papers after deduplication: {len(paper_overview)}')
display(source_overview)
display(year_overview)
display(paper_overview)
```

#### Code Cell 7

```python
import os
import shutil

resources_root = project_root / 'resources'
pdfs_root = resources_root / 'pdfs'
resources_root.mkdir(exist_ok=True)
pdfs_root.mkdir(exist_ok=True)

with sqlite3.connect(project_root / 'project.db') as connection:
    pdf_resources = pd.read_sql_query(
        """
        SELECT
            records.canonical_id,
            records.title,
            records.year,
            records.first_author,
            records.venue,
            records.doi,
            records.oa_status,
            records.license,
            downloads.resolver_source,
            downloads.file_path AS original_file_path
        FROM downloads
        JOIN records ON records.id = downloads.record_id
        WHERE downloads.status = 'success'
          AND LOWER(downloads.file_format) = 'pdf'
        ORDER BY records.year DESC, records.title
        """,
        connection,
    )

mapped_rows = []
for paper in pdf_resources.to_dict('records'):
    source_path = project_root / paper['original_file_path']
    destination_path = pdfs_root / f"{paper['canonical_id']}.pdf"

    if not source_path.exists() or source_path.read_bytes()[:5] != b'%PDF-':
        print(f"Skipped invalid or missing PDF: {source_path}")
        continue

    if not destination_path.exists():
        try:
            os.link(source_path, destination_path)
        except OSError:
            shutil.copy2(source_path, destination_path)

    paper['resource_pdf'] = str(destination_path.relative_to(project_root))
    mapped_rows.append(paper)

pdf_manifest = pd.DataFrame(mapped_rows)
csv_path = resources_root / 'pdf_resources.csv'
markdown_path = resources_root / 'pdf_resources.md'
pdf_manifest.to_csv(csv_path, index=False)

markdown_columns = [
    'canonical_id', 'title', 'year', 'first_author', 'doi',
    'resolver_source', 'resource_pdf', 'original_file_path',
]
markdown_table = pdf_manifest.reindex(columns=markdown_columns).fillna('')
markdown_lines = [
    '# Downloaded PDF resources',
    '',
    'This manifest contains only successful open-access PDF downloads.',
    '',
]
if markdown_table.empty:
    markdown_lines.append('No PDFs have been downloaded yet.')
else:
    markdown_lines.extend([
        '| ' + ' | '.join(markdown_columns) + ' |',
        '| ' + ' | '.join(['---'] * len(markdown_columns)) + ' |',
    ])
    for row in markdown_table.itertuples(index=False, name=None):
        values = [str(value).replace('|', '\\|').replace('\n', ' ') for value in row]
        markdown_lines.append('| ' + ' | '.join(values) + ' |')
markdown_path.write_text('\n'.join(markdown_lines) + '\n', encoding='utf-8')

print(f'Resources folder: {resources_root}')
print(f'PDF folder: {pdfs_root}')
print(f'CSV manifest: {csv_path}')
print(f'Markdown manifest: {markdown_path}')
print(f'Mapped PDFs: {len(pdf_manifest)}')

if pdf_manifest.empty:
    print('No open-access PDFs have been downloaded yet.')
    print('After committing title/abstract include decisions, run:')
    print(f'  {sys.executable} scripts/05_resolve_oa.py --project {project_id}')
    print(f'  {sys.executable} scripts/06_download.py --project {project_id}')
else:
    display(pdf_manifest)
```

#### Code Cell 8

```python
# Prepare an auditable screening batch, then obtain one advisory result from SURF AI-HUB.
from dotenv import load_dotenv
import os
import re
import requests

with sqlite3.connect(project_root / 'project.db') as connection:
    existing_decision_count = connection.execute(
        'SELECT COUNT(*) FROM screening WHERE decision IS NOT NULL'
    ).fetchone()[0]

batch_files = sorted((project_root / 'screening').glob('batch_*.jsonl'))
if existing_decision_count:
    print(f'Reusing {existing_decision_count} existing screening decision(s); deduplication is skipped.')
elif batch_files:
    print('Reusing an existing unreviewed screening batch; deduplication is skipped.')
else:
    dedup_result = subprocess.run(
        [
            sys.executable,
            'scripts/03_dedup.py',
            '--project',
            project_id,
            '--acknowledge-warnings',
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    print(dedup_result.stdout)
    if dedup_result.returncode:
        print(dedup_result.stderr)
        raise RuntimeError(f'Deduplication failed with exit code {dedup_result.returncode}.')

    batch_result = subprocess.run(
        [
            sys.executable,
            'scripts/04_screen_prep.py',
            '--project',
            project_id,
            '--batch-size',
            '5',
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    print(batch_result.stdout)
    if batch_result.returncode:
        print(batch_result.stderr)
        raise RuntimeError(f'Screening-batch preparation failed with exit code {batch_result.returncode}.')
    batch_files = sorted((project_root / 'screening').glob('batch_*.jsonl'))
if not batch_files:
    raise FileNotFoundError('No screening batch was created from the retrieved evidence.')

with batch_files[0].open(encoding='utf-8') as batch_file:
    candidate = json.loads(next(batch_file))

candidate_summary = pd.DataFrame(
    [
        {
            'title': candidate.get('title'),
            'year': candidate.get('year'),
            'first_author': candidate.get('first_author'),
            'source_url': candidate.get('url'),
        }
    ]
)
display(candidate_summary)

# Configuration follows the working WILLMA stress-test contract.
SURF_DISCOVERY_URL = 'https://api.willma.surf.nl/v0/sequences'
SURF_CHAT_URL = 'https://willma.surf.nl/api/v0/chat/completions'
CONNECT_TIMEOUT_SECONDS = 30
READ_TIMEOUT_SECONDS = 180
MINIMUM_QWEN_PARAMETERS_B = 32

env_path = repo_root / '.env'
if not env_path.exists():
    raise FileNotFoundError(f'Missing SURF AI-HUB configuration file: {env_path}')

load_dotenv(env_path, override=True)
surf_api_key = os.getenv('SURF_AI_HUB_API_KEY', '').strip()
if not surf_api_key:
    raise RuntimeError('SURF_AI_HUB_API_KEY is missing from .env.')

surf_headers = {
    'X-API-KEY': surf_api_key,
    'Content-Type': 'application/json',
}

discovery_response = requests.get(
    SURF_DISCOVERY_URL,
    headers=surf_headers,
    timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
)
print(f'SURF AI-HUB model discovery status: {discovery_response.status_code}')
if discovery_response.status_code in {401, 403}:
    raise RuntimeError(
        'SURF AI-HUB rejected SURF_AI_HUB_API_KEY. Verify that the key is current and '
        'authorized for the WILLMA model-discovery endpoint.'
    )
discovery_response.raise_for_status()
models_payload = discovery_response.json()
if not isinstance(models_payload, list):
    raise RuntimeError('SURF AI-HUB model discovery returned an unexpected payload.')

models_df = pd.DataFrame(models_payload)
if 'sequence_type' not in models_df.columns:
    models_df['sequence_type'] = 'unknown'
if 'name' not in models_df.columns:
    raise RuntimeError('SURF AI-HUB model discovery did not return model names.')

def qwen_parameter_count_b(model_name):
    match = re.search(r'(?<!\d)(\d+)\s*b(?:\b|[-_])', str(model_name), flags=re.IGNORECASE)
    return int(match.group(1)) if match else None

def is_eligible_qwen_model(model_name, sequence_type):
    normalized_name = str(model_name).casefold()
    return (
        str(sequence_type).casefold() == 'text'
        and 'qwen' in normalized_name
        and '2.5' in normalized_name
        and 'instruct' in normalized_name
        and (qwen_parameter_count_b(model_name) or 0) >= MINIMUM_QWEN_PARAMETERS_B
    )

eligible_models = sorted(
    [
        (qwen_parameter_count_b(row['name']), row['name'])
        for _, row in models_df.iterrows()
        if is_eligible_qwen_model(row['name'], row.get('sequence_type', 'unknown'))
    ],
    reverse=True,
)
available_model_names = set(models_df['name'].dropna().astype(str))
requested_model = os.getenv('SURF_AI_HUB_MODEL', '').strip()

if requested_model:
    if requested_model not in available_model_names:
        raise RuntimeError(f'SURF_AI_HUB_MODEL is not visible to this API key: {requested_model}')
    if not any(model_name == requested_model for _, model_name in eligible_models):
        raise RuntimeError(
            f'SURF_AI_HUB_MODEL must be a Qwen 2.5 Instruct text model with at least '
            f'{MINIMUM_QWEN_PARAMETERS_B}B parameters: {requested_model}'
        )
    selected_model = requested_model
elif eligible_models:
    selected_model = eligible_models[0][1]
else:
    discovered_text_models = models_df.loc[
        models_df['sequence_type'].astype(str).str.casefold().eq('text'),
        'name',
    ].dropna().astype(str).tolist()
    raise RuntimeError(
        'No Qwen 2.5 Instruct model with at least '
        f'{MINIMUM_QWEN_PARAMETERS_B}B parameters is available. '
        f'Discovered text models: {discovered_text_models}'
    )

display(models_df[[column for column in ['id', 'name', 'sequence_type', 'latency_mode'] if column in models_df.columns]])
print(f'Selected SURF AI-HUB model: {selected_model}')

prompt = f'''You are an evidence-screening advisor for a systematic literature review.
Research topic: The Problem With Using AI to Review AI-Written Code.

Apply these criteria:
- Include empirical studies, benchmarks, or systematic evaluations of AI-assisted or AI-driven code review, code analysis, or defect detection.
- Exclude opinion-only work, general code-generation work without review or evaluation, and records with insufficient metadata.

Return exactly these fields:
Decision: include, exclude, or uncertain
Reason: one or two sentences
Criteria: relevant inclusion or exclusion IDs
Human review required: yes

Candidate title: {candidate.get('title', 'Unavailable')}
Candidate abstract: {candidate.get('abstract') or 'Unavailable'}
'''

chat_payload = {
    'model': selected_model,
    'max_tokens': 350,
    'system': (
        'Provide a cautious, evidence-bound recommendation. '
        'Do not claim that the recommendation is a final screening decision.'
    ),
    'messages': [{'role': 'user', 'content': prompt}],
}
chat_response = requests.post(
    SURF_CHAT_URL,
    headers=surf_headers,
    json=chat_payload,
    timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
)
print(f'SURF AI-HUB advisory status: {chat_response.status_code}')
chat_response.raise_for_status()
chat_result = chat_response.json()

def extract_response_text(payload):
    choices = payload.get('choices', []) if isinstance(payload, dict) else []
    if not choices:
        return str(payload)
    content = choices[0].get('message', {}).get('content', '')
    if isinstance(content, list):
        return ''.join(
            item.get('text', '') if isinstance(item, dict) else str(item)
            for item in content
        )
    return str(content)

usage = chat_result.get('usage', {}) if isinstance(chat_result, dict) else {}
recommendation_table = pd.DataFrame(
    [
        {
            'candidate_title': candidate.get('title'),
            'surf_ai_hub_model': selected_model,
            'surf_advisory': extract_response_text(chat_result),
            'human_decision_required': 'Yes - no screening decision was written',
        }
    ]
)
display(recommendation_table)
display(
    pd.DataFrame(
        [
            {
                'input_tokens': usage.get('prompt_tokens'),
                'output_tokens': usage.get('completion_tokens'),
                'total_tokens': usage.get('total_tokens'),
            }
        ]
    )
)
```

#### Code Cell 9

```python
reviewed_decisions = {
    1: {
        'decision': 'include',
        'reason': 'Empirical evaluation of neural automated code review at scale; reports dataset, methods, performance challenges, and limitations.',
        'criteria_hit': ['I1', 'I2', 'I3'],
    },
    2: {
        'decision': 'include',
        'reason': 'Empirical study of a fine-tuned LLM for automated code review, evaluating accuracy and comprehensibility.',
        'criteria_hit': ['I1', 'I2', 'I3'],
    },
    3: {
        'decision': 'include',
        'reason': 'Reports an automated code-review tool evaluated in an industrial development workflow.',
        'criteria_hit': ['I1', 'I2', 'I3'],
    },
    4: {
        'decision': 'exclude',
        'reason': 'Broad cybersecurity and privacy discussion; it does not evaluate AI-assisted code review, code analysis, or defect detection.',
        'criteria_hit': ['E1', 'E2'],
    },
    5: {
        'decision': 'include',
        'reason': 'Quantitative and qualitative evaluation of LLM-based automated code review with reported outcomes.',
        'criteria_hit': ['I1', 'I2', 'I3'],
    },
}

batch_path = project_root / 'screening' / 'batch_001.jsonl'
labeled_rows = []
with batch_path.open(encoding='utf-8') as batch_file:
    for line in batch_file:
        record = json.loads(line)
        assessment = reviewed_decisions.get(record['record_id'])
        if assessment:
            record.update(assessment)
        labeled_rows.append(record)

with batch_path.open('w', encoding='utf-8') as batch_file:
    for record in labeled_rows:
        batch_file.write(json.dumps(record, ensure_ascii=False) + '\n')

for command in (
    [
        sys.executable, 'scripts/04b_screen_commit.py',
        '--batch', str(batch_path), '--decided-by', 'agent',
    ],
    [sys.executable, 'scripts/05_resolve_oa.py', '--project', project_id],
    [sys.executable, 'scripts/06_download.py', '--project', project_id],
):
    result = subprocess.run(command, cwd=repo_root, text=True, capture_output=True)
    print(result.stdout)
    if result.returncode:
        print(result.stderr)
        raise RuntimeError(f'Command failed: {" ".join(command)}')
```

#### Code Cell 10

```python
arxiv_decisions = {
    52: 'Empirical user study of explainability, trust, and agreement in LLM-assisted code review.',
    53: 'Large-scale empirical analysis of developer responses to agent-generated code review comments.',
    54: 'Empirical study of 1.02 million pull requests measuring AI reviewer effects on efficiency and quality.',
    58: 'Benchmark-based study of AI self-review failure modes when reviewing AI-generated code.',
    59: 'Eye-tracking experiment examining human review behavior for LLM-generated code.',
}

with sqlite3.connect(project_root / 'project.db') as connection:
    candidate_rows = pd.read_sql_query(
        """
        SELECT id AS record_id, canonical_id, title, abstract, year, first_author, venue, doi
        FROM records
        WHERE id IN (52, 53, 54, 58, 59)
        ORDER BY id
        """,
        connection,
    ).to_dict('records')

arxiv_batch_path = project_root / 'screening' / 'batch_002.jsonl'
with arxiv_batch_path.open('w', encoding='utf-8') as batch_file:
    for record in candidate_rows:
        record.update({
            'batch_id': 'batch_002',
            'decision': 'include',
            'reason': arxiv_decisions[record['record_id']],
            'criteria_hit': ['I1', 'I2', 'I3'],
        })
        batch_file.write(json.dumps(record, ensure_ascii=False) + '\n')

for command in (
    [
        sys.executable, 'scripts/04b_screen_commit.py',
        '--batch', str(arxiv_batch_path), '--decided-by', 'agent',
    ],
    [sys.executable, 'scripts/05_resolve_oa.py', '--project', project_id, '--retry-failed'],
    [sys.executable, 'scripts/06_download.py', '--project', project_id, '--retry-failed'],
):
    result = subprocess.run(command, cwd=repo_root, text=True, capture_output=True)
    print(result.stdout)
    if result.returncode:
        print(result.stderr)
        raise RuntimeError(f'Command failed: {" ".join(command)}')
```

#### Code Cell 11

```python
from datetime import datetime, timezone
import json
import re

# Render a compact, auditable Markdown overview from the project database.
report_path = project_root / 'ai_written_code_review.md'
report_terms = (
    'code review', 'automated code review', 'ai code review', 'llm',
    'large language model', 'generated code', 'code generation',
    'agent-generated', 'self-review', 'human oversight',
)

def markdown_text(value):
    return str(value or '').replace('|', '\\|').replace('\n', ' ').strip()

def metadata_text(value):
    text = '' if pd.isna(value) else str(value).strip()
    return '' if text.lower() == 'nan' else text

def apa_initials(given):
    return ' '.join(f'{part[0]}.' for part in re.findall(r"[A-Za-z]+", metadata_text(given)))

def apa_authors(authors_json, fallback):
    try:
        authors = json.loads(metadata_text(authors_json))
    except json.JSONDecodeError:
        authors = []
    names = [
        f"{metadata_text(author.get('family'))}, {apa_initials(author.get('given'))}".rstrip(', ')
        for author in authors[:20]
        if metadata_text(author.get('family'))
    ]
    if len(authors) > 20:
        names = names[:19] + ['...'] + names[-1:]
    if not names:
        return metadata_text(fallback) or 'Unknown author'
    if len(names) == 1:
        return names[0]
    return ', '.join(names[:-1]) + ', & ' + names[-1]

def markdown_table(columns, rows):
    lines = [
        '| ' + ' | '.join(columns) + ' |',
        '| ' + ' | '.join(['---'] * len(columns)) + ' |',
    ]
    for row in rows:
        lines.append('| ' + ' | '.join(markdown_text(value) for value in row) + ' |')
    return '\n'.join(lines)

with sqlite3.connect(project_root / 'project.db') as connection:
    records = pd.read_sql_query(
        """
        SELECT
            r.id, r.canonical_id, r.title, r.abstract, r.year, r.authors_json, r.first_author,
            r.venue, r.doi, r.url, bm.container_title, bm.volume, bm.issue, bm.pages, bm.publisher,
            GROUP_CONCAT(DISTINCT sh.source) AS sources,
            s.decision, s.reason, s.criteria_hit,
            MAX(CASE WHEN d.status = 'success' AND LOWER(d.file_format) = 'pdf' THEN 1 ELSE 0 END) AS has_pdf
        FROM records r
        LEFT JOIN source_hits sh ON sh.record_id = r.id
        LEFT JOIN screening s ON s.record_id = r.id AND s.pass = 'title_abstract'
        LEFT JOIN bibliographic_metadata bm ON bm.record_id = r.id
        LEFT JOIN downloads d ON d.record_id = r.id
        GROUP BY r.id
        """,
        connection,
    )
    source_counts = pd.read_sql_query(
        "SELECT source, COUNT(DISTINCT record_id) AS records FROM source_hits GROUP BY source ORDER BY records DESC, source",
        connection,
    )
    screening_counts = pd.read_sql_query(
        "SELECT decision, COUNT(*) AS records FROM screening WHERE pass = 'title_abstract' GROUP BY decision ORDER BY decision",
        connection,
    )
    download_counts = pd.read_sql_query(
        "SELECT status, COUNT(DISTINCT record_id) AS records FROM downloads GROUP BY status ORDER BY status",
        connection,
    )

records['title'] = records['title'].fillna('Untitled record')
records['abstract'] = records['abstract'].fillna('')
records['matched_terms'] = records.apply(
    lambda record: [
        term for term in report_terms
        if term in f"{record['title']} {record['abstract']}".lower()
    ],
    axis=1,
)
records['relevance_score'] = records['matched_terms'].str.len()
records.loc[records['decision'].eq('include'), 'relevance_score'] += 4
records.loc[records['has_pdf'].eq(1), 'relevance_score'] += 2
records['ranking_reason'] = records.apply(
    lambda record: '; '.join(
        ([f"matched: {', '.join(record['matched_terms'])}"] if record['matched_terms'] else [])
        + (['title/abstract included'] if record['decision'] == 'include' else [])
        + (['open-access PDF downloaded'] if record['has_pdf'] else [])
    ) or 'metadata-only match',
    axis=1,
)
ranked_records = records.sort_values(
    ['relevance_score', 'has_pdf', 'year', 'title'],
    ascending=[False, False, False, True],
).reset_index(drop=True)
ranked_records.index += 1

query_files = {
    'OpenAlex': 'openalex.txt',
    'arXiv': 'arxiv.txt',
    'Semantic Scholar': 'semantic_scholar.txt',
    'Crossref': 'crossref.json',
}
queries = {
    source: (project_root / 'queries' / filename).read_text(encoding='utf-8').strip()
    for source, filename in query_files.items()
}

source_rows = source_counts[['source', 'records']].itertuples(index=False, name=None)
screening_rows = screening_counts[['decision', 'records']].itertuples(index=False, name=None)
download_rows = download_counts[['status', 'records']].itertuples(index=False, name=None)
ranking_rows = []
for rank, record in ranked_records.head(20).iterrows():
    author = apa_authors(record['authors_json'], record['first_author'])
    year = int(record['year']) if pd.notna(record['year']) else 'n.d.'
    sources = metadata_text(record['sources']) or 'unknown source'
    ranking_rows.append((
        rank,
        f"**{record['title']}**<br>{author} ({year})",
        f"**Score: {record['relevance_score']}**<br>{record['ranking_reason']}<br>Sources: {sources}",
    ))

reference_records = ranked_records.copy()
reference_records['reference_author'] = reference_records['first_author'].map(metadata_text).str.casefold()
reference_records = reference_records.sort_values(['reference_author', 'year', 'title'], na_position='last')
reference_lines = []
for _, record in reference_records.iterrows():
    author = apa_authors(record['authors_json'], record['first_author'])
    year = int(record['year']) if pd.notna(record['year']) else 'n.d.'
    venue_name = metadata_text(record['venue'])
    container_title = metadata_text(record['container_title']) or venue_name
    publisher = metadata_text(record['publisher'])
    volume = metadata_text(record['volume'])
    issue = metadata_text(record['issue'])
    pages = metadata_text(record['pages'])
    doi = metadata_text(record['doi'])
    url = metadata_text(record['url'])
    venue = f" <em>{container_title}</em>" if container_title else ''
    if volume:
        venue += f", <em>{volume}</em>"
    if issue:
        venue += f"({issue})"
    if pages:
        venue += f", {pages}"
    if not venue and publisher:
        venue = f" {publisher}"
    if venue:
        venue += '.'
    doi_url = f"https://doi.org/{doi}"
    doi_link = f" <a href=\"{doi_url}\">{doi_url}</a>" if doi else ''
    url_link = f" <a href=\"{url}\">{url}</a>" if not doi and url else ''
    reference_lines.append(
        f"<li>{author} ({year}). {record['title']}.{venue}{doi_link or url_link}</li>"
    )

report_lines = [
    '# AI-Written Code Review: Evidence Overview',
    '',
    '## Contents',
    '',
    '- [Scope](#scope)',
    '- [Provenance and Notebook Development](#provenance-and-notebook-development)',
    '- [Search Method](#search-method)',
    '- [Relevance Ranking](#relevance-ranking)',
    '- [Relevant Sources Found Through SLR](#relevant-sources-found-through-slr)',
    '- [Reproducibility Notes](#reproducibility-notes)',
    '- [Appendix A. Verantwoording en correcties](#appendix-a-verantwoording-en-correcties)',
    '',
    f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
    '',
    '## Scope',
    '',
    '**Topic:** An automated, AI-assisted systematic literature review addressing:',
    '',
    f"**{topic}**",
    '',
    '**Aim:** To synthesize empirical evidence on the reliability, risks, and forms of human oversight required when AI systems evaluate AI-generated code.',
    '',
    'This report presents a reproducible, auditable overview of the current [SLR-Engine](https://github.com/tuirk/SLR-Engine) project. It distinguishes retrieved evidence, AI-assisted screening recommendations, and the transparent ranking heuristic used to support inspection; it does not treat automated output as a substitute for scholarly judgement.',
    '',
    '## Provenance and Notebook Development',
    '',
    'This notebook is based on [SLR-Engine](https://github.com/tuirk/SLR-Engine), an auditable workflow for systematic literature reviews. It uses a SURF AI-HUB Qwen 2.5 Instruct model only for bounded screening advice; final decisions remain subject to human review.',
    '',
    'The notebook persists literal source queries, retrieves and deduplicates records, prepares screening batches, records reviewed decisions, resolves lawful open-access copies, validates downloaded PDFs, and exports this evidence overview. Source provenance, decisions, download outcomes, and ranking signals remain database-backed so the workflow can be rerun and extended without treating model output as final scholarly judgement.',
    '',
    '## Search Method',
    '',
    'The notebook searched OpenAlex, Crossref, arXiv, and Semantic Scholar with a cap of 25 source hits per source. Any source failure remains an audit limitation rather than evidence of no results.',
    '',
    '### Literal Queries',
    '',
]
for source, query in queries.items():
    report_lines.extend([f'**{source}**', '', '```text', query, '```', ''])
report_lines.extend([
    '### Retrieval and Processing Audit',
    '',
    f"Canonical records after deduplication: **{len(records)}**.",
    '',
    markdown_table(['Source', 'Distinct records'], source_rows),
    '',
    'Title/abstract screening decisions are recorded with stated reasons and criteria in the project database.',
    '',
    markdown_table(['Decision', 'Records'], screening_rows),
    '',
    'Download outcomes represent lawful open-access retrieval attempts only; publisher-blocked or closed content is not bypassed.',
    '',
    markdown_table(['Download status', 'Records'], download_rows),
    '',
    '## Relevance Ranking',
    '',
    'Ranking is an inspection aid, not an inclusion decision. Score = number of matched topic terms + 4 for a committed title/abstract include decision + 2 for a verified downloaded open-access PDF. The rationale is listed for each paper.',
    '',
    '<details>',
    '<summary>Top 20 ranked records <sub>inspection aid</sub></summary>',
    '',
    markdown_table(['Rank', 'Paper', 'Evidence'], ranking_rows),
    '',
    '</details>',
    '',
    'The table is limited to the 20 highest-ranked records; the complete metadata remains in the project database and source inventory below.',
    '',
    '## Relevant Sources Found Through SLR',
    '',
    'This inventory contains the deduplicated records retrieved by the SLR workflow from OpenAlex, Crossref, arXiv, and Semantic Scholar. Entries use APA 7-style author, date, title, source, volume, issue, pages, and DOI/URL formatting when metadata is available. DOI URLs are retained. DOI-bearing records are enriched from Crossref and cached in the local audit database; records without a DOI or unavailable Crossref metadata retain the source fields provided by the original search result. Appearing here does not by itself indicate a final eligibility decision, methodological-quality assessment, or full-text review.',
    '',
    '<details>',
    '<summary>Complete source inventory <sub>deduplicated records</sub></summary>',
    '',
    '<ol>',
    '',
] + reference_lines + [
    '</ol>',
    '',
    '</details>',
    '',
    '## Reproducibility Notes',
    '',
    '- Query files, source hits, deduplication, screening decisions, download attempts, and local PDF paths are retained in the project directory and SQLite audit database.',
    '- SURF AI-HUB advice is model-selected at runtime and displayed without writing a decision; the selected model and request scope should be recorded before any publication use.',
    '- Results should be reviewed before publication, especially metadata-only records and screening decisions.',
    '',
    '## Appendix A. Verantwoording en correcties',
    '',
    'Deze rapportage is opgesteld met ondersteuning van generatieve AI. De auteur blijft verantwoordelijk voor de onderzoeksopzet, de controle van de feiten, de selectie van bronnen, de inhoudelijke interpretatie en de uiteindelijke tekst. AI-uitvoer is gebruikt als ondersteuning en niet als zelfstandig bewijs of als vervanging van menselijk oordeel.',
    '',
    '### Gebruikte AI-ondersteuning',
    '',
    markdown_table(['Tool of component', 'Rol in deze rapportage', 'Beheersmaatregel'], [
        ('SURF AI-HUB Qwen 2.5 Instruct model (minimaal 32B)', 'Begrensd advies bij screening van een kandidaatrecord.', 'Model is runtime geselecteerd; advies schrijft geen beslissing en vereist menselijke beoordeling.'),
        ('SLR-Engine workflow', 'Herleidbare zoek-, deduplicatie-, screening- en exportstappen.', 'Queries, bronhits, beslissingen en downloaduitkomsten blijven lokaal auditbaar.'),
    ]),
    '',
    '### Juridische en ethische uitgangspunten',
    '',
    '- **Artikel 5 AVG:** doelbinding en dataminimalisatie zijn relevant voor zover in de workflow persoonsgegevens worden verwerkt.',
    '- **Artikel 12 AVG:** informatie over verwerking van persoonsgegevens moet duidelijk en toegankelijk zijn wanneer betrokkenen moeten worden geinformeerd.',
    '- **Artikel 13 AI Act:** bevat transparantieverplichtingen voor hoog-risico-AI-systemen; de bepaling is alleen van toepassing wanneer een systeem onder die categorie valt.',
    '- **Artikel 50 AI Act:** bevat specifieke transparantieverplichtingen, onder meer rond AI-interactie en bepaalde synthetische inhoud. De toepasselijkheid hangt af van de concrete inzet en rol van het AI-systeem.',
    '',
    'Deze appendix is een transparantieverklaring voor deze rapportage en geen juridisch advies. Bij verwerking van persoonsgegevens of inzet in een gereguleerde context is aanvullende toetsing nodig.',
    '',
    '## Appendix B. Reproducible Procedure and Code-Cell Explanation',
    '',
    'This appendix describes the executable V04 workflow as implemented. A data scientist can reproduce the local evidence workflow without treating the AI response as a final scholarly decision.',
    '',
    '### Prerequisites',
    '',
    '1. Open `SLR_Engine_V04_SURF_AI_HUB_Demo.ipynb` from the SLR-Engine repository root.',
    '2. Select the `prisma-env` Jupyter kernel and install the repository dependencies in that environment.',
    '3. Create a repository-root `.env` file containing `SURF_AI_HUB_API_KEY=<key>`. Optionally set `SURF_AI_HUB_MODEL=<visible eligible model name>` to pin a model; otherwise the notebook selects the largest eligible model.',
    '4. Ensure outbound HTTPS access to OpenAlex, Crossref, arXiv, Semantic Scholar, `https://api.willma.surf.nl`, and `https://willma.surf.nl`. Search results and visible models vary by date, network, API key, and source availability.',
    '5. Run the notebook in order. Do not rerun deduplication after screening decisions exist; the notebook intentionally reuses existing batches in that case.',

    '### Code Cells and Their Exact Role',

    '1. **Kernel verification.** Prints the executable, Python version, and environment prefix, then raises an error unless the active interpreter belongs to `prisma-env`. This prevents a notebook from silently running in the base Conda environment.',
    '2. **Repository verification.** Confirms `README.md`, `scripts/`, `slr_engine/`, and `tests/` exist below the current working directory, then runs `pytest -q` with the active interpreter. It stops on test failure before project data is changed.',
    '3. **Project and protocol initialization.** Creates or reuses `projects/Willma_SLR`, then writes `project.yaml` with the topic, aim, research questions, inclusion criteria I1-I3, exclusion criteria E1-E3, seed placeholders, and `agent` as the advisory provider.',
    '4. **Protocol display.** Renders the saved protocol as a pandas table. It is a review checkpoint: verify the research question and eligibility criteria before any retrieval.',
    '5. **Bounded literature search.** Writes literal query files under `projects/Willma_SLR/queries/`, calls `scripts/02_search_open.py` for OpenAlex, Crossref, arXiv, and Semantic Scholar with a 25-record-per-source cap, then queries `project.db` to display the first ten provenance-backed records.',
    '6. **Retrieved-evidence inspection.** Reads all database records and source hits, calculates a transparent count of topic-term signals, and displays per-source, per-year, and per-paper tables. This score only prioritizes inspection; it is not a screening decision.',
    '7. **PDF resources map.** Reads successful PDF downloads, validates the `%PDF-` signature, hard-links or copies each valid file to `projects/Willma_SLR/resources/pdfs/`, and writes CSV and Markdown manifests with source and resolver provenance.',
    '8. **SURF AI-HUB advisory call.** Reuses an existing unreviewed screening batch or runs `03_dedup.py` and `04_screen_prep.py`. It sends one candidate title and abstract to SURF AI-HUB, discovers models through `/v0/sequences`, requires a text Qwen 2.5 Instruct model with at least 32B parameters, and posts a bounded advisory prompt to `/api/v0/chat/completions`. The displayed response, selected model, and token usage are advisory evidence only; this cell does not write a screening decision.',
    '9. **First reviewed batch and downloads.** Writes demo labels for `batch_001.jsonl`, commits them with `04b_screen_commit.py`, resolves lawful open-access locations with `05_resolve_oa.py`, and downloads with `06_download.py`. Replace the example labels and reasons with independently reviewed judgements before using this as a study dataset. The `--decided-by agent` value is provenance metadata, not evidence that an AI may make final decisions.',
    '10. **Additional reviewed batch.** Selects the five hard-coded database record IDs 52, 53, 54, 58, and 59, writes `batch_002.jsonl`, commits the supplied include labels, then retries OA resolution and downloads. These IDs are specific to the saved demo database and must be replaced by stable canonical identifiers or a human-selected query in a fresh reproduction.',
    '11. **Evidence report export.** Reads the SQLite audit tables and query files, calculates the report ranking, creates an HTML-compatible APA-style reference list from available metadata, and writes `projects/Willma_SLR/ai_written_code_review.md`. Its ranking is exactly: matched topic-term count + 4 for a committed include decision + 2 for a verified downloaded PDF.',
    '12. **Compact ranking refresh.** Replaces only the generated report ranking section using the in-memory ranked records. It is a formatting refresh and must be run after the report-export cell in the same kernel.',
    '13. **Standalone APA-style export.** Reads `project.db` independently and writes `projects/Willma_SLR/references_apa.md`. It preserves source-limited first-author metadata and must not be interpreted as a fully verified APA bibliography.',

    '### AI and SLR Decision Boundary',

    '- The AI service receives one selected candidate title and abstract, not repository source code and not an entire screening batch.',
    '- The model prompt requires `Decision`, `Reason`, `Criteria`, and `Human review required: yes`; its response is displayed but never inserted into the `screening` table by the advisory cell.',
    '- SLR inclusion and exclusion decisions must be reviewed against I1-I3 and E1-E3, documented with reasons, and retained in `project.db` and JSONL batch files.',
    '- Downloading is limited to resolver-discovered open-access copies; failed or blocked downloads remain audit outcomes and must not be bypassed.',
    '- Reproducibility means preserving the notebook version, package versions, literal query files, source timestamps, project database, batch JSONL files, model name, prompt, raw response, and human-decision provenance. It does not mean that a future source search or model call will return identical results.',

    '### Expected Outputs',

    '- `projects/Willma_SLR/project.yaml`: protocol and configuration.',
    '- `projects/Willma_SLR/project.db`: records, source hits, screening, and download audit trail.',
    '- `projects/Willma_SLR/queries/`: literal source queries.',
    '- `projects/Willma_SLR/screening/`: prepared and reviewed JSONL batches.',
    '- `projects/Willma_SLR/resources/`: verified PDF map and manifests when lawful PDFs are available.',
    '- `projects/Willma_SLR/ai_written_code_review.md` and `references_apa.md`: human-readable evidence and source-metadata exports.',

])

# Embed the executable notebook source so this report remains self-contained.
notebook_path = repo_root / 'SLR_Engine_V04_SURF_AI_HUB_Demo.ipynb'
notebook_document = json.loads(notebook_path.read_text(encoding='utf-8'))
report_lines.extend([
    '### Verbatim Code by Cell',
    '',
    'The following blocks are copied directly from the notebook source at report-generation time. They contain no secret values; API keys are read from `.env` at runtime.',
    '',
])
code_cell_number = 0
for notebook_cell in notebook_document['cells']:
    if notebook_cell.get('cell_type') != 'code':
        continue
    code_cell_number += 1
    report_lines.extend([
        f'#### Code Cell {code_cell_number}',
        '',
        '```python',
        ''.join(notebook_cell.get('source', [])).rstrip(),
        '```',
        '',
    ])
report_path.write_text('\n'.join(report_lines), encoding='utf-8')
print(f'Wrote report: {report_path}')
print(f'Ranked records: {len(ranked_records)}')
display(ranked_records.head(20)[['title', 'year', 'relevance_score', 'ranking_reason']])
```

#### Code Cell 12

```python
from pathlib import Path

import json
import re
import sqlite3

import pandas as pd

repo_root = Path.cwd().resolve()
project_root = repo_root / 'projects' / 'Willma_SLR'
project_db = project_root / 'project.db'
apa_references_path = project_root / 'references_apa.md'

if not project_db.exists():
    raise FileNotFoundError(f'Willma project database is missing: {project_db}')


def reference_value(value):
    text = '' if pd.isna(value) else str(value).strip()
    return '' if text.lower() == 'nan' else text


def apa_initials(given):
    return ' '.join(f'{part[0]}.' for part in re.findall(r"[A-Za-z]+", reference_value(given)))


def apa_authors(authors_json, fallback):
    try:
        authors = json.loads(reference_value(authors_json))
    except json.JSONDecodeError:
        authors = []
    names = [
        f"{reference_value(author.get('family'))}, {apa_initials(author.get('given'))}".rstrip(', ')
        for author in authors[:20]
        if reference_value(author.get('family'))
    ]
    if len(authors) > 20:
        names = names[:19] + ['...'] + names[-1:]
    if not names:
        return reference_value(fallback) or 'Unknown author'
    if len(names) == 1:
        return names[0]
    return ', '.join(names[:-1]) + ', & ' + names[-1]


with sqlite3.connect(project_db) as connection:
    reference_records = pd.read_sql_query(
        '''
        SELECT r.authors_json, r.first_author, r.year, r.title, r.venue, r.doi, r.url,
               bm.container_title, bm.volume, bm.issue, bm.pages, bm.publisher
        FROM records r
        LEFT JOIN bibliographic_metadata bm ON bm.record_id = r.id
        ORDER BY LOWER(COALESCE(r.first_author, '')), r.year, r.title
        ''',
        connection,
    )

apa_references = []
for _, record in reference_records.iterrows():
    author = apa_authors(record['authors_json'], record['first_author'])
    year = int(record['year']) if pd.notna(record['year']) else 'n.d.'
    title = reference_value(record['title']) or 'Untitled record'
    venue = reference_value(record['container_title']) or reference_value(record['venue'])
    volume = reference_value(record['volume'])
    issue = reference_value(record['issue'])
    pages = reference_value(record['pages'])
    publisher = reference_value(record['publisher'])
    doi = reference_value(record['doi'])
    url = reference_value(record['url'])
    source_url = f'https://doi.org/{doi}' if doi else url
    venue_part = f' *{venue}*' if venue else (f' {publisher}' if publisher else '')
    if volume:
        venue_part += f', *{volume}*'
    if issue:
        venue_part += f'({issue})'
    if pages:
        venue_part += f', {pages}'
    if venue_part:
        venue_part += '.'
    source_part = f' {source_url}' if source_url else ''
    apa_references.append(f'{author} ({year}). {title}.{venue_part}{source_part}')

apa_references_path.write_text(
    '\n'.join([
        '# Relevant Sources Found Through SLR (APA 7-Style)',
        '',
        'Generated from retrieved Willma_SLR metadata. Author lists are formatted from stored `authors_json` values and DOI URLs are retained. DOI-bearing records are enriched from Crossref with source, volume, issue, page, and publisher metadata when available; records without a DOI or unavailable Crossref metadata retain their original search fields. Verify entries against the original publication before formal citation or publication use.',
        '',
        *[f'{number}. {reference}' for number, reference in enumerate(apa_references, start=1)],
        '',
    ]),
    encoding='utf-8',
)

print(f'Wrote {len(apa_references)} APA-style references: {apa_references_path}')
```

#### Code Cell 13

```python
from pathlib import Path

import json
import re
import sqlite3

import pandas as pd

repo_root = Path.cwd().resolve()
project_root = repo_root / 'projects' / 'Willma_SLR'
project_db = project_root / 'project.db'
apa_references_path = project_root / 'references_apa.md'

if not project_db.exists():
    raise FileNotFoundError(f'Willma project database is missing: {project_db}')


def reference_value(value):
    text = '' if pd.isna(value) else str(value).strip()
    return '' if text.lower() == 'nan' else text


def apa_initials(given):
    return ' '.join(f'{part[0]}.' for part in re.findall(r"[A-Za-z]+", reference_value(given)))


def apa_authors(authors_json, fallback):
    try:
        authors = json.loads(reference_value(authors_json))
    except json.JSONDecodeError:
        authors = []
    names = [
        f"{reference_value(author.get('family'))}, {apa_initials(author.get('given'))}".rstrip(', ')
        for author in authors[:20]
        if reference_value(author.get('family'))
    ]
    if len(authors) > 20:
        names = names[:19] + ['...'] + names[-1:]
    if not names:
        return reference_value(fallback) or 'Unknown author'
    if len(names) == 1:
        return names[0]
    return ', '.join(names[:-1]) + ', & ' + names[-1]


with sqlite3.connect(project_db) as connection:
    reference_records = pd.read_sql_query(
        '''
        SELECT r.authors_json, r.first_author, r.year, r.title, r.venue, r.doi, r.url,
               bm.container_title, bm.volume, bm.issue, bm.pages, bm.publisher
        FROM records r
        LEFT JOIN bibliographic_metadata bm ON bm.record_id = r.id
        ORDER BY LOWER(COALESCE(r.first_author, '')), r.year, r.title
        ''',
        connection,
    )

apa_references = []
for _, record in reference_records.iterrows():
    author = apa_authors(record['authors_json'], record['first_author'])
    year = int(record['year']) if pd.notna(record['year']) else 'n.d.'
    title = reference_value(record['title']) or 'Untitled record'
    venue = reference_value(record['container_title']) or reference_value(record['venue'])
    volume = reference_value(record['volume'])
    issue = reference_value(record['issue'])
    pages = reference_value(record['pages'])
    publisher = reference_value(record['publisher'])
    doi = reference_value(record['doi'])
    url = reference_value(record['url'])
    source_url = f'https://doi.org/{doi}' if doi else url
    venue_part = f' *{venue}*' if venue else (f' {publisher}' if publisher else '')
    if volume:
        venue_part += f', *{volume}*'
    if issue:
        venue_part += f'({issue})'
    if pages:
        venue_part += f', {pages}'
    if venue_part:
        venue_part += '.'
    source_part = f' {source_url}' if source_url else ''
    apa_references.append(f'{author} ({year}). {title}.{venue_part}{source_part}')

apa_references_path.write_text(
    '\n'.join([
        '# Relevant Sources Found Through SLR (APA 7-Style)',
        '',
        'Generated from retrieved Willma_SLR metadata. Author lists are formatted from stored `authors_json` values and DOI URLs are retained. DOI-bearing records are enriched from Crossref with source, volume, issue, page, and publisher metadata when available; records without a DOI or unavailable Crossref metadata retain their original search fields. Verify entries against the original publication before formal citation or publication use.',
        '',
        *[f'{number}. {reference}' for number, reference in enumerate(apa_references, start=1)],
        '',
    ]),
    encoding='utf-8',
)

print(f'Wrote {len(apa_references)} APA-style references: {apa_references_path}')
```

</details>

## Appendix C. Recipe: Reusing the Workflow for a New Clinical-Reasoning Topic

SEE also: https://github.com/HR-AI-HUB/hr-ai-hub.github.io/blob/main/SLR-ENGINE/NandA-found-sources-on-clinical-reasoning-through-SLR.md

<details>
<summary>Clinical-reasoning reuse recipe <sub>companion protocol-design example</sub></summary>

This recipe adapts the workflow and bounded WILLMA advisory step to **the use of NANDA-I, NIC, and NOC terminologies to improve clinical reasoning through generative-AI-based agents**. It is a protocol-design example, not a completed clinical review or clinical decision support.

### 1. Define the Review Boundary

Approve the protocol before searching. Define the care setting, reasoning activity, AI-agent intervention, terminology role, outcomes, and exclusions. For example:

> In clinical settings, how are generative-AI-based agents that use NANDA-I, NIC, and/or NOC terminologies evaluated for supporting clinical reasoning, and what evidence exists concerning accuracy, safety, usability, and human oversight?

| Concept | Operational meaning |
| --- | --- |
| NANDA-I | Standardized nursing diagnoses. |
| NIC | Nursing Interventions Classification. |
| NOC | Nursing Outcomes Classification. |
| Generative-AI agent | An LLM-based system that generates, explains, retrieves, or proposes information in a multi-step workflow. |
| Clinical reasoning support | Assistance with assessment, diagnosis, intervention planning, outcome reasoning, explanation, or reflection; not autonomous care decisions. |

Confirm terminology names, editions, licences, and care context with domain experts. Mentioning a terminology alone is not evidence of clinical-reasoning support.

### 2. Create a New, Isolated Project

Do not overwrite `projects/Willma_SLR`. Copy the structure to a new directory such as `projects/Clinical_Reasoning_Terminologies_SLR`, then update its configuration, queries, report name, and screening batches. Use a new SQLite database to prevent records and decisions from being mixed across topics.

Before searching, replace the topic, aim, research questions, I1-I3 criteria, E1-E3 criteria, and literal queries in the protocol-initialization cell.

### 3. Define Eligibility Criteria

| Criterion | Example rule |
| --- | --- |
| I1: Topic | Evaluates NANDA-I, NIC, NOC, standardized nursing terminologies, or a clearly mapped equivalent in a clinical-reasoning context. |
| I2: Intervention | Evaluates generative AI, an LLM, a conversational agent, or an agentic workflow. |
| I3: Evidence | Reports empirical evaluation, a benchmark, validation, user study, implementation study, or systematic review with methods and findings. |
| E1: Not clinical reasoning | Does not address assessment, diagnosis, interventions, outcomes, or reasoning support. |
| E2: Not generative AI | Describes only rule-based, statistical, or administrative software. |
| E3: Insufficient evidence | Is an editorial, marketing item, duplicate, or lacks sufficient detail for relevance assessment. |

Obtain clinician or nursing-informatics approval before committing labels.

### 4. Write and Run Literal Queries

Store source-specific queries under the new project's `queries/` directory. Retain syntax, dates, limits, results, and any amendment. A starting query is:

```text
("NANDA-I" OR NANDA OR "Nursing Interventions Classification" OR NIC OR "Nursing Outcomes Classification" OR NOC OR "standardized nursing terminology")
AND ("clinical reasoning" OR "clinical decision making" OR "nursing diagnosis" OR "care planning")
AND ("generative AI" OR "large language model" OR LLM OR "AI agent" OR "conversational agent")
```

For sources with limited Boolean support, use focused alternatives such as `NANDA-I large language model`, `NIC NOC AI agent`, and `nursing diagnosis generative AI`. Retrieve, deduplicate, and inspect early results for false positives. Ranking remains an inspection aid, never an inclusion rule.

### 5. Keep WILLMA Bounded to Screening Advice

Send only one candidate title and abstract, the question, and eligibility criteria. Request a tentative decision, short reason, applicable criteria, and explicit human review. Add this constraint:

```text
Do not provide patient-specific diagnostic, treatment, intervention, or outcome recommendations.
Assess only whether the publication appears eligible for this literature review from its title and abstract.
```

Never send patient records, case notes, identifiers, unpublished clinical data, or licensed terminology content. The advice remains reviewer-visible only until a qualified human independently records a reason.

### 6. Screen, Extract, and Synthesize with Human Oversight

For each included study, record the care setting, task, terminology integration, agent architecture, model and retrieval sources, comparator, evaluation method, outcomes, limitations, and oversight. Assess accuracy, calibration, safety, usability, workload, equity, and implementation separately where possible. Do not infer clinical validity from fluent output, terminology use, or one accuracy score.

Use lawful open-access retrieval and respect licences, confidentiality, and copyright. Preserve the notebook version, dependencies, queries, timestamps, database, reviewed batches, selected model, prompt, advisory response, and reviewer provenance. Obtain clinical, methodological, privacy, and terminology-governance review before publication or operational use.

### Recipe Checklist

1. Create a separate project folder and database.
2. Replace the protocol, criteria, and queries for the new topic.
3. Retrieve and deduplicate records; inspect early results manually.
4. Use WILLMA only for one-record title-and-abstract screening advice.
5. Commit only human-reviewed screening and extraction decisions.
6. Respect open-access, terminology-licence, privacy, and governance boundaries.
7. Report evidence alongside explicit safety, validity, and oversight limitations.

</details>

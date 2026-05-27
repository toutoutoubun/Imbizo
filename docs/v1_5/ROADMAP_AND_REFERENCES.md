## 10a. Roadmap delta

### What v1.5 enables that v1.0 could not

v1.0 made code-switching annotation deeper by adding noun class, concord, and
4-M evidence. v1.5 changes the scale of the questions researchers can ask. It
does not make the software more authoritative. It makes uncertainty, local
variation, and exchange with other research communities easier to document.

First, v1.5 lets a project treat sister-language ambiguity as a research object
rather than a nuisance. A researcher can now ask: "Across this corpus of
multilingual township interviews, can we distinguish isiZulu utterances from
isiXhosa utterances even where their morphology is shared?" (# fictional /
paraphrased research question). The answer may be yes for some tokens, no for
others, and "not enough evidence" for many. That mixed result is more honest
than forcing every Nguni token into a single label. The same applies to
Sesotho/Setswana and the optional Northern Sotho comparison, where form-level
similarity must be interpreted alongside speaker, place, and genre (Mesthrie,
2002, 2008).

Second, v1.5 supports triggered-switching analysis as a different lens from MLF.
A researcher can ask: "When speakers switch from Sesotho to English, what
proportion of switches is preceded by an English proper noun within the previous
two tokens?" (# fictional / paraphrased research question; Clyne, 1967, 2003).
This does not prove intention. It lets the researcher compare confirmed trigger
candidates across speakers, scenes, and topics, then return to the excerpts for
conversation-level interpretation (Auer, 1998).

Third, v1.5 makes mixed-code variety analysis possible without pretending that
living varieties are dictionary objects. A project can ask: "Does our data
contain Tsotsitaal-flavored lexis, and if so, under what conversational
conditions does it appear?" (# fictional / paraphrased research question;
Slabbert & Myers-Scotton, 1997; Hurst, 2008). The answer must remain cautious:
the detector reports lexical evidence only, and the researcher must decide
whether Tsotsitaal, Iscamtho, Kaaps, Sabela, or a project-local label fits the
ethnographic context (McCormick, 2002; Ntshangase, 2002).

Fourth, v1.5 extends borrowing integration beyond morphology. A researcher can
ask whether phonological adaptation gives a sharper distinction between
borrowings and switches than noun-class and concord evidence alone (# fictional /
paraphrased research question; Poplack, 1980; Muysken, 2000). If a word carries
host morphology but no audible phonological adaptation, that matters. If it
carries both, that also matters. The v2 score keeps the weights visible so that
the theory remains the researcher's, not the software's.

Finally, v1.5 makes comparative exchange more realistic. A project can ask:
"Can our findings be exchanged with LIDES-based and CHAT/CLAN-based researchers
without losing what makes them ours?" (# fictional / paraphrased research
question; Barnett et al., 2000; MacWhinney, 2000). The answer is not a simple
yes. Transcript text, speakers, time alignment, and language labels can travel.
Some Imbizo-specific evidence must travel as sidecar metadata and validation
reports. That is still progress: losses become documented, reproducible, and
citable rather than silent.

Across all five changes, v1.5 turns "edge cases" into visible parts of the
method. Ambiguous sister-language tokens, possible triggers, mixed-code spans,
phonological cues, and export losses are no longer scattered in private notes.
They become reviewable records that can be filtered, reported, challenged, and
cited. That matters for humanities researchers because the point is not only to
count language choices, but to explain how the evidence was made.

### What is now feasible for v2.0

1. **Speaker-Turn CS Profile dashboard** - v2.0 can build offline, per-speaker,
per-scene, and per-topic visualizations over the evidence now stored in v1.5.
Sankey diagrams, timeline summaries, and turn-level CS profiles should be
rendered locally as SVG or static images. They must remain exploratory views,
not automatic interpretations of identity or intent.

2. **Local ASR plug-in support** - The v1.5 plug-in and offline-bundle patterns
make it feasible to support Whisper.cpp, Vosk, or comparable local ASR engines
as optional downloads. ASR must remain separate from the core installer, with
explicit per-language quality disclaimers and no claim that automatic
transcription is equally reliable across South African languages (Yilmaz et al.,
2018).

3. **Localized UIs** - v2.0 can prioritize Afrikaans, isiZulu, isiXhosa,
Sesotho, and Setswana interface catalogs. Localization should include not only
menus but also metric explanations, warnings, caveats, and consent language.
Community review should be used for UI strings that carry theoretical or
ethical weight.

4. **Reviewer constellations** - v1.5 review packets support one reviewer at a
time. v2.0 can support offline reviewer constellations: multiple reviewer
aliases, relationship-to-project metadata, disagreement histories, and
side-by-side comments. Disagreement must remain visible instead of being merged
into a single consensus label.

5. **Extended language coverage** - Sepedi, siSwati, Xitsonga, Tshivenda, and
isiNdebele can become first-class once project dictionaries, UI labels, and
review workflows are ready. The v1.5 per-pair dictionary architecture gives a
path for adding coverage without pretending that one Bantu-language heuristic
works for all languages.

6. **Optional, opt-in LLM-assisted synthetic-data augmentation** - A future
plug-in could help generate synthetic examples for training or documentation,
but only behind PRINCIPLES.md, explicit consent, local or user-controlled
runtime options, and clear labeling that generated examples are not corpus
evidence. It must never become required for core annotation, metrics, or export.

### What remains out of scope, and why

Cloud sync remains out of scope because it conflicts with offline-first design
and data sovereignty. A future plug-in could exist only for projects with
explicit consent, local institutional approval, end-to-end encryption controlled
by the researcher, and no default upload behavior.

A mandatory LLM dependency remains out of scope because it would violate the
no-subscription, no-API-key, no-cloud principle. An opt-in LLM plug-in could
exist only if it is clearly separated from the core, never used for hidden
annotation, and governed by project ethics, community consent, and reproducible
logging.

Automatic interpretation of CS meaning remains out of scope. The literature
licenses candidate evidence, structural analysis, trigger hypotheses, and
interactional readings, not a black-box declaration of why a speaker switched.
Any future assistance must present evidence and competing interpretations, not
final meanings.

Anonymous telemetry remains out of scope because it creates hidden extraction
from research environments. A future diagnostic export could exist only as a
manual, local file the researcher chooses to send, after inspecting its contents
and removing project data.

### Governance note

Dictionary contributions and community-review packets should feed into shipped
dictionaries through an offline-friendly path: exported review zips, plain-text
patches, and human-readable diffs that can be carried by USB and submitted later
when connectivity is available. Review disagreements must be preserved as
evidence rather than averaged into a false consensus. In line with the CARE
Principles, shipped resources should reflect collective benefit, authority to
control, responsibility, and ethics, especially when dictionaries touch
stigmatized varieties or community-specific language knowledge (Carroll et al.,
2020).

## 10b. Consolidated references

Adebara, I., Elmadany, A., Abdul-Mageed, M., & Alcoba Inciarte, A. (2022).
AfroLID: A neural language identification tool for African languages. *EMNLP
2022*. https://aclanthology.org/2022.emnlp-main.128/

Ali, S. M. (2016). A brief introduction to decolonial computing. *XRDS:
Crossroads*, 22(4), 16-21.

Al-Rfou, R., Perozzi, B., & Skiena, S. (2013). Polyglot: Distributed word
representations for multilingual NLP. *CoNLL 2013*.

Auer, P. (Ed.). (1998). *Code-switching in conversation: Language, interaction
and identity*. Routledge.

Barnett, R., Codo, E., Eppler, E., Forcadell, M., Gardner-Chloros, P., van
Hout, R., et al. (2000). The LIDES Coding Manual. *International Journal of
Bilingualism*, 4(2).

Boersma, P., & Weenink, D. (2024). *Praat: Doing phonetics by computer*.
https://www.fon.hum.uva.nl/praat/

Carroll, S. R., Garba, I., Figueroa-Rodriguez, O. L., Holbrook, J., Lovett, R.,
Materechera, S., et al. (2020). The CARE Principles for Indigenous Data
Governance. *Data Science Journal*, 19(1), 43.

Chue Hong, N. P., et al. (2022). *FAIR Principles for Research Software
(FAIR4RS Principles)*. Research Data Alliance.

Clyne, M. (1967). *Transference and triggering*. Martinus Nijhoff.

Clyne, M. (2003). *Dynamics of language contact*. Cambridge University Press.

Cole, D. T. (1955). *An introduction to Tswana grammar*. Longmans Green.

Cozien, C. (2020). *Code-switching among bilingual speakers of Cape Muslim
Afrikaans and South African English in the Bo-Kaap, Cape Town* [MA thesis,
University of Cape Town].

Demuth, K. (2000). Bantu noun class systems: Loanword and acquisition evidence
of semantic productivity. In G. Senft (Ed.), *Systems of nominal classification*
(pp. 270-292). Cambridge University Press.

Doke, C. M. (1927). *Textbook of Zulu grammar*. Maskew Miller Longman.

Doke, C. M., & Mofokeng, S. M. (1957). *Textbook of Southern Sotho grammar*.
Maskew Miller Longman.

Du Plessis, J. A., & Visser, M. (1992). *Xhosa syntax*. Via Afrika.

Eiselen, R., & Puttkammer, M. J. (2014). Developing text resources for ten South
African languages. *LREC 2014*.

Goh, K.-I., & Barabasi, A.-L. (2008). Burstiness and memory in complex systems.
*EPL*, 81(4), 48002.

Guerois, R. (2014). The noun class system of Cuwabo and related Bantu languages.
*Africana Linguistica*, 20.

Guzman, G. A., Ricard, J., Serigos, J., Bullock, B. E., & Toribio, A. J. (2017).
Metrics for modeling code-switching across corpora. *INTERSPEECH 2017*.

Hendricks, F. (2016). The nature and context of Kaaps: A contemporary, past and
future perspective. *Multilingual Margins*, 3(2).

Hurst, E. (2008). *Style, structure and function in Cape Town Tsotsitaal* [PhD
dissertation, University of Cape Town].

Hyman, L. M. (2003). Segmental phonology. In D. Nurse & G. Philippson (Eds.),
*The Bantu languages* (pp. 42-58). Routledge.

Jake, J. L., Myers-Scotton, C., & Gross, S. (2002). Making a minimalist approach
to codeswitching work: Adding the Matrix Language. *Bilingualism: Language and
Cognition*, 5(1), 69-91.

Joulin, A., Grave, E., Bojanowski, P., & Mikolov, T. (2017). Bag of tricks for
efficient text classification. *EACL 2017*.

Kargaran, A. H., Yvon, F., & Schutze, H. (2024). MaskLID: Code-switching
language identification through iterative masking. *ACL 2024*.

Kodali, P., Goel, A., Choudhury, M., Shrivastava, M., & Kumaraguru, P. (2022).
SyMCoM - Syntactic measure of code mixing. *Findings of ACL 2022*.

Lombard, D. P. (1985). *Introduction to the grammar of Northern Sotho*. Van
Schaik.

Mabokela, R., & Schlippe, T. (2022). A sentiment corpus for South African
under-resourced languages in a multilingual context. *SIGUL @ LREC 2022*.

MacWhinney, B. (2000). *The CHILDES project: Tools for analyzing talk* (3rd
ed.). Lawrence Erlbaum Associates.

Mahomed, S., Maritz, J., Scholtz, L., Barnard, E., & Heerden, C. van. (2019).
Prevalence of code mixing in semi-formal patient communication in low-resource
languages of South Africa. *arXiv:1911.05636*.

Maho, J. F. (1999). *A comparative study of Bantu noun classes*. Acta
Universitatis Gothoburgensis.

McCormick, K. (2002). *Language in Cape Town's District Six*. Oxford University
Press.

Mesthrie, R. (Ed.). (2002). *Language in South Africa*. Cambridge University
Press.

Mesthrie, R. (2008). "Death of the mother tongue" - is English a glottophagic
language in South Africa? *English Today*, 24(2).

Mojapelo, M. L. (2007). *Definiteness in Northern Sotho* [PhD dissertation,
Stellenbosch University].

Muysken, P. (2000). *Bilingual speech: A typology of code-mixing*. Cambridge
University Press.

Myers-Scotton, C. (1993). *Duelling languages: Grammatical structure in
codeswitching*. Oxford University Press.

Myers-Scotton, C. (2002). *Contact linguistics: Bilingual encounters and
grammatical outcomes*. Oxford University Press.

Nel, J. H. (2012). *Grammatical and socio-pragmatic aspects of conversational
code switching by Afrikaans-English bilingual children* [MA thesis,
Stellenbosch University].

Ntshangase, D. K. (2002). Language and language practices in Soweto. In R.
Mesthrie (Ed.), *Language in South Africa* (pp. 407-415). Cambridge University
Press.

Poplack, S. (1980). Sometimes I'll start a sentence in Spanish y termino en
espanol. *Linguistics*, 18(7/8), 581-618.

Poulos, G., & Msimang, C. T. (1998). *A linguistic analysis of Zulu*. Via
Afrika.

Risam, R. (2018). *New digital worlds: Postcolonial digital humanities in
theory, praxis, and pedagogy*. Northwestern University Press.

Slabbert, S., & Myers-Scotton, C. (1997). The structure of Tsotsitaal and
Iscamtho: Code-switching and in-group identity in South African townships.
*Linguistics*, 35(2).

Smith, A. M., Katz, D. S., Niemeyer, K. E., & FORCE11 Software Citation Working
Group. (2016). Software citation principles. *PeerJ Computer Science*, 2, e86.

Stell, G. (2010). Ethnicity in linguistic variation: White and Coloured
identities in Afrikaans-English code-switching. *Pragmatics*, 20(3).

Taljard, E., & Bosch, S. E. (2006). A comparison of approaches to word-class
tagging. *Nordic Journal of African Studies*, 15(4).

Vandeghinste, V., et al. (2025). AfroCS-xs: Creating a compact, high-quality,
human-validated code-switched dataset for African languages. *ACL 2025*.

Van der Westhuizen, E., & Niesler, T. R. (2018). A first South African corpus of
multilingual code-switched soap opera speech. *LREC 2018*.

Wittenburg, P., Brugman, H., Russel, A., Klassmann, A., & Sloetjes, H. (2006).
ELAN: A professional framework for multimodality research. *LREC 2006*.

Yilmaz, E., Biswas, A., Van der Westhuizen, E., De Wet, F., & Niesler, T.
(2018). Building a unified code-switching ASR system for South African
languages. *INTERSPEECH 2018*.

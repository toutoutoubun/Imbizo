## 10a. Roadmap delta

### What v1.0 Enables That MVP Could Not

The MVP made it possible to keep interview data local, annotate code-switching at token level, and export reproducible metrics. Version 1.0 changes the grain of analysis. It lets a researcher ask not only which languages appear in an utterance, but how borrowed, inserted, or alternated material is being fitted into the grammar around it. For Bantu languages, that matters because grammatical work is often carried by noun classes and concord relations rather than by word order alone (Demuth, 2000; Poulos & Msimang, 1998). A surface label such as `eng` or `zul` can show that a switch exists, but it cannot show whether an English noun is behaving as a bare English item or as a noun integrated into an isiZulu, isiXhosa, Sesotho, or Setswana agreement frame.

In practical terms, v1.0 makes questions like this answerable: "Across this corpus of isiZulu-English interviews, which noun classes most often host English loanwords, and does this pattern differ by speaker generation?" The example is fictional or paraphrased, but the research move is real: the researcher can now combine token annotations, noun-class fields, speaker metadata, and exportable tables to compare patterns across people, scenes, or registers. This supports qualitative interpretation without reducing the corpus to a single score.

The Concord Agreement Tracker adds another layer. A researcher can ask whether a foreign-language stem is accompanied by host-language concords: for example, whether a fictional or paraphrased phrase such as `i-laptop entsha` is treated as a class 9 noun with an agreeing adjective in isiZulu. This is not automatic proof of borrowing or Matrix Language status, but it is evidence that can be inspected, accepted, rejected, memoed, and exported.

The 4-M annotation layer then gives v1.0 leverage that MVP Matrix Language and Embedded Language labels could not provide. Myers-Scotton's System Morpheme Principle claims that certain late system morphemes are supplied by the Matrix Language in classic Matrix Language Frame analysis (Myers-Scotton, 1993, 2002). With v1.0, a researcher can ask: "Are outsider late system morphemes in mixed isiZulu-Afrikaans utterances drawn consistently from isiZulu, consistent with MLF's System Morpheme Principle?" This question remains interpretive, but it is now tied to visible token-level evidence rather than an impressionistic statement.

Version 1.0 also makes register-sensitive questions easier. A researcher can compare how the integration-score distribution shifts between formal interview talk and informal aside talk, or whether a speaker uses more concord-integrated English nouns in classroom examples than in narrative reflection. Those scores are transparent and editable because different theoretical traditions weigh borrowing, insertion, and alternation differently (Poplack, 1980; Muysken, 2000). The result is a workbench that can support grammatical, sociolinguistic, and discourse-analytic questions without pretending that the software has interpreted the social meaning of the switch for the researcher.

### What Is Now Feasible for v1.5

1. **Sister-language disambiguator (zul vs xho, sot vs tsn).** v1.0 now stores enough morphology-aware evidence to make a local, rule-based disambiguator plausible, but it could not be done responsibly in v1.0 because the shipped dictionaries are starter resources and many entries still require speaker review. A v1.5 disambiguator should use distinctive morpheme lists, click-orthography frequency cues for isiXhosa, and carefully reviewed minimum-pair lexicons. It must report uncertainty plainly because isiZulu and isiXhosa, and Sesotho and Setswana, overlap in ways that a researcher may need to interpret in context rather than have flattened by software.

2. **Triggered-switching detector.** Clyne's trigger hypothesis can now be explored as a local, rule-based candidate flagger rather than as an automatic explanation (Clyne, 1967, 2003). v1.5 can scan around known trigger words, cognates, named entities, and recent switch points, then surface candidate trigger contexts for the researcher to confirm or dismiss. The feature should write provenance for every accepted trigger and avoid declaring causality.

3. **Borrowing integration score refinements.** v1.0 defines a transparent morphology-and-concord based integration score. v1.5 can refine it with tonal or phonological adaptation criteria, but only where community input and language-specific expertise support those criteria. Phonological adaptation is analytically important, yet it is also easy to overgeneralize from written transcripts, so any new criterion must be optional, documented, and sensitivity-testable.

4. **Comparable subcorpus exporter.** v1.0's richer annotations make it feasible to export comparable subcorpora for international comparison, including LIDES-oriented structures and CHAT/CLAN-friendly formats (Barnett et al., 2000). This would help researchers participate in wider code-switching research without abandoning ELAN, Praat, Excel, or the local project folder. The exporter should preserve provenance and dictionary versions so comparisons remain reproducible.

5. **Tsotsitaal / Iscamtho / Kaaps mode.** v1.0 already refuses to force all data into standard-language assumptions. v1.5 can make that stance more explicit with a mixed-code variety mode for Tsotsitaal, Iscamtho, Kaaps, and related user-defined varieties, informed by work on urban South African code-switching and identity (Slabbert & Myers-Scotton, 1997). This mode should change defaults, warnings, and dictionary behavior, not impose a separate hierarchy of "correct" forms.

### What Remains Out of Scope, and Why

**Cloud sync** remains out of scope because it conflicts with offline-first operation and data sovereignty. A future plug-in could support user-managed local or institutional storage only if a project ethics file explicitly permits it, no account system is required, and the sync target is chosen by the researcher rather than by the application.

**A required LLM dependency** remains out of scope because it would introduce cloud, API-key, licensing, or hardware assumptions that violate the project's no-subscription and no-telemetry principles. An opt-in plug-in could later exist only for bounded tasks, with explicit informed consent, local-project provenance, and a visible warning that the model is not an interpreter of participant meaning.

**Bundled large-vocabulary ASR** remains out of scope because it would undermine the low-resource hardware target. Local ASR plug-ins may be acceptable when they can run offline, be disabled completely, and present transcripts as editable drafts rather than authoritative text.

**Automatic interpretation of code-switching meaning** remains out of scope because Imbizo-CS is humanities-led. A future advisory tool may help retrieve examples, concordances, or researcher memos, but it must never decide the social, identity, pragmatic, or political meaning of a switch for the researcher.

### Governance Note

v1.5 and later should be shaped by community review, not only by software planning. Each Bantu language dictionary needs native-speaker reviewers and researchers familiar with local language practices. The project should support an offline-friendly contribution path, including USB-transferred patch bundles for researchers without persistent internet. A community advisory board representing South African researchers and indigenous-language communities should guide dictionary acceptance, terminology, and data-governance defaults in line with the CARE Principles for Indigenous Data Governance (Carroll et al., 2020).

## 10b. Consolidated references

Adebara, I., Elmadany, A., Abdul-Mageed, M., & Alcoba Inciarte, A. (2022). AfroLID: A neural language identification tool for African languages. *EMNLP 2022*. https://aclanthology.org/2022.emnlp-main.128/

Ali, S. M. (2016). A brief introduction to decolonial computing. *XRDS: Crossroads*, 22(4), 16-21.

Al-Rfou, R., Perozzi, B., & Skiena, S. (2013). Polyglot: Distributed word representations for multilingual NLP. *CoNLL 2013*.

Auer, P. (Ed.). (1998). *Code-switching in conversation: Language, interaction and identity*. Routledge.

Barnett, R., Codo, E., Eppler, E., Forcadell, M., Gardner-Chloros, P., van Hout, R., et al. (2000). The LIDES Coding Manual. *International Journal of Bilingualism*, 4(2).

Boersma, P., & Weenink, D. (2024). *Praat: Doing phonetics by computer*. https://www.fon.hum.uva.nl/praat/

Carroll, S. R., Garba, I., Figueroa-Rodriguez, O. L., Holbrook, J., Lovett, R., Materechera, S., et al. (2020). The CARE Principles for Indigenous Data Governance. *Data Science Journal*, 19(1), 43.

Chue Hong, N. P., et al. (2022). *FAIR Principles for Research Software (FAIR4RS Principles)*. Research Data Alliance.

Clyne, M. (1967). *Transference and triggering*. Martinus Nijhoff.

Clyne, M. (2003). *Dynamics of language contact*. Cambridge University Press.

Cole, D. T. (1955). *An introduction to Tswana grammar*. Longmans Green.

Cozien, C. (2020). *Code-switching among bilingual speakers of Cape Muslim Afrikaans and South African English in the Bo-Kaap, Cape Town* [MA thesis, University of Cape Town].

Demuth, K. (2000). Bantu noun class systems: Loanword and acquisition evidence of semantic productivity. In G. Senft (Ed.), *Systems of nominal classification* (pp. 270-292). Cambridge University Press.

Doke, C. M. (1927). *Textbook of Zulu grammar*. Maskew Miller Longman.

Du Plessis, J. A., & Visser, M. (1992). *Xhosa syntax*. Via Afrika.

Eiselen, R., & Puttkammer, M. J. (2014). Developing text resources for ten South African languages. *LREC 2014*.

Goh, K.-I., & Barabasi, A.-L. (2008). Burstiness and memory in complex systems. *EPL*, 81(4), 48002.

Guerois, R. (2014). The noun class system of Cuwabo and related Bantu languages. *Africana Linguistica*, 20.

Guzman, G. A., Ricard, J., Serigos, J., Bullock, B. E., & Toribio, A. J. (2017). Metrics for modeling code-switching across corpora. *INTERSPEECH 2017*.

Jake, J. L., Myers-Scotton, C., & Gross, S. (2002). Making a minimalist approach to codeswitching work: Adding the Matrix Language. *Bilingualism: Language and Cognition*, 5(1), 69-91.

Joulin, A., Grave, E., Bojanowski, P., & Mikolov, T. (2017). Bag of tricks for efficient text classification. *EACL 2017*.

Kargaran, A. H., Yvon, F., & Schutze, H. (2024). MaskLID: Code-switching language identification through iterative masking. *ACL 2024*.

Kodali, P., Goel, A., Choudhury, M., Shrivastava, M., & Kumaraguru, P. (2022). SyMCoM - Syntactic measure of code mixing. *Findings of ACL 2022*.

Mabokela, R., & Schlippe, T. (2022). A sentiment corpus for South African under-resourced languages in a multilingual context. *SIGUL @ LREC 2022*.

Mahomed, S., Maritz, J., Scholtz, L., Barnard, E., & Heerden, C. van. (2019). Prevalence of code mixing in semi-formal patient communication in low-resource languages of South Africa. *arXiv:1911.05636*.

Maho, J. F. (1999). *A comparative study of Bantu noun classes*. Acta Universitatis Gothoburgensis.

Mojapelo, M. L. (2007). *Definiteness in Northern Sotho* [PhD dissertation, Stellenbosch University].

Muysken, P. (2000). *Bilingual speech: A typology of code-mixing*. Cambridge University Press.

Myers-Scotton, C. (1993). *Duelling languages: Grammatical structure in codeswitching*. Oxford University Press.

Myers-Scotton, C. (2002). *Contact linguistics: Bilingual encounters and grammatical outcomes*. Oxford University Press.

Nel, J. H. (2012). *Grammatical and socio-pragmatic aspects of conversational code switching by Afrikaans-English bilingual children* [MA thesis, Stellenbosch University].

Poplack, S. (1980). Sometimes I'll start a sentence in Spanish y termino en espanol. *Linguistics*, 18(7/8), 581-618.

Poulos, G., & Msimang, C. T. (1998). *A linguistic analysis of Zulu*. Via Afrika.

Risam, R. (2018). *New digital worlds: Postcolonial digital humanities in theory, praxis, and pedagogy*. Northwestern University Press.

Slabbert, S., & Myers-Scotton, C. (1997). The structure of Tsotsitaal and Iscamtho. *Linguistics*, 35(2).

Smith, A. M., Katz, D. S., Niemeyer, K. E., & FORCE11 Software Citation Working Group. (2016). Software citation principles. *PeerJ Computer Science*, 2, e86.

Stell, G. (2010). Ethnicity in linguistic variation: White and Coloured identities in Afrikaans-English code-switching. *Pragmatics*, 20(3).

Taljard, E., & Bosch, S. E. (2006). A comparison of approaches to word-class tagging. *Nordic Journal of African Studies*, 15(4).

Vandeghinste, V., et al. (2025). AfroCS-xs. *ACL 2025*.

Van der Westhuizen, E., & Niesler, T. R. (2018). A first South African corpus of multilingual code-switched soap opera speech. *LREC 2018*.

Wittenburg, P., Brugman, H., Russel, A., Klassmann, A., & Sloetjes, H. (2006). ELAN: A professional framework for multimodality research. *LREC 2006*.

Yilmaz, E., Biswas, A., Van der Westhuizen, E., De Wet, F., & Niesler, T. (2018). Building a unified code-switching ASR system for South African languages. *INTERSPEECH 2018*.

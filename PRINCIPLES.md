# PRINCIPLES.md
## The constitution of Imbizo-CS Workbench
### Imbizo-CS Workbench の憲法

---

## Preamble — 前文

This document is the constitution of the Imbizo-CS Workbench codebase. It exists to ensure that future contributors, reviewers, and downstream researchers can understand not only **how** this software is built, but **why** it is built the way it is — and **what it must refuse to become**.

本文書は Imbizo-CS Workbench のコードベースの憲法である。将来の貢献者・査読者・下流の研究者が、このソフトウェアが **どのように** 構築されているかだけでなく、**なぜ** そのように構築されているか、そして **何になることを拒むか** を理解できるようにするために存在する。

If you are reading this because you intend to contribute, modify, fork, or build upon this software, please read this document **before** the source code. The technical implementation is downstream of these commitments. If a future change to the code would erode a principle stated here, that change is a regression — regardless of how much it improves user experience, performance, feature coverage, or test scores.

もし貢献・修正・フォーク・派生を意図してこれを読んでいるなら、ソースコードを読む前にこの文書を読んでほしい。技術的実装はこれらの誓約の下流にある。ここに述べられた原則を侵食するコード変更は、ユーザー体験・性能・機能カバレッジ・テストスコアをどれほど向上させようとも、退化（regression）である。

---

## Part I — Foundational principles
## 第I部 — 基礎原則

### 1. Ten non-negotiables

These ten principles are non-negotiable. Every design decision, every prompt, every test, every line of code must be evaluable against them.

これら10の原則は妥協不能である。すべての設計判断、すべてのプロンプト、すべてのテスト、すべてのコード行は、これらに照らして評価可能でなければならない。

1. **Offline-first.** All core features function without internet. Bootstrap is the only network-using component.
   オフライン・ファースト。すべてのコア機能はインターネットなしで動作する。Bootstrap のみがネットワークを使う唯一のコンポーネントである。

2. **Data sovereignty.** Research data lives on the researcher's local machine. Nothing is uploaded. No telemetry. No analytics.
   データ主権。研究データは研究者のローカル機器に存在する。何もアップロードしない。テレメトリーなし。アナリティクスなし。

3. **Low-resource by design.** The software must run on a CPU-only laptop with 4–8 GB RAM, including older or second-hand hardware.
   低資源前提設計。CPU のみ・4〜8 GB RAM のラップトップ（中古・旧型を含む）で動作しなければならない。

4. **Humanities-led; automation is auxiliary.** Every automatic decision is overridable. The researcher is the final arbiter.
   人文学主導。自動化は補助である。すべての自動判定は上書き可能であり、研究者が最終判断者である。

5. **Incremental knowledge-building.** Imperfect automatic analysis must never block scholarly progress.
   漸進的知識構築。不完全な自動解析が学問的前進を妨げてはならない。

6. **No subscription, no API key, no cloud, no telemetry.** These are not features; they are categorical exclusions.
   サブスクリプションなし、API キーなし、クラウドなし、テレメトリーなし。これらは機能ではなく、絶対的な排除である。

7. **Open-source dependencies only.** Proprietary tools are excluded by design, not by oversight.
   オープンソース依存のみ。プロプライエタリツールは見落としではなく、設計上排除される。

8. **Interoperable with existing humanities workflows.** ELAN, Praat, Excel / LibreOffice Calc, LIDES, CHAT/CLAN.
   既存の人文学ワークフローとの相互運用性。ELAN、Praat、Excel / LibreOffice Calc、LIDES、CHAT/CLAN。

9. **Citable and reproducible.** Every analysis step is logged with provenance and can be reconstructed from exported data.
   引用可能・再現可能。すべての解析ステップは provenance とともに記録され、エクスポートされたデータから再構築できる。

10. **Decolonial computing posture.** The defaults must not assume English-medium, global-North research infrastructure.
    脱植民地的コンピューティングの姿勢。デフォルトはグローバルノースの英語主導研究インフラを前提としてはならない。

### 2. Tiebreakers

When two or more principles conflict, prefer in this order:

複数の原則が衝突するとき、以下の順序で優先する:

1. Offline operation. オフライン動作
2. Data sovereignty. データ主権
3. Researcher's interpretive authority. 研究者の解釈権限
4. Linguistic dignity of the communities represented in the data. データに表象される共同体の言語的尊厳
5. Reproducibility and citability. 再現可能性と引用可能性
6. Backward compatibility with prior project versions. 過去バージョンとの後方互換性
7. Theoretical pluralism (MLF, Muyskenian, Poplackian, CA, decolonial sociolinguistics). 理論的多元主義

---

## Part II — Why morphology matters
## 第II部 — なぜ形態論が重要か

### 1. Whitespace tokenisation is a colonial inheritance for Bantu languages

For English and Afrikaans, the whitespace-delimited word is a workable unit of analysis. For isiZulu, isiXhosa, Sesotho, Setswana — and for every other Bantu language in our scope — it is not. A token such as `Ngithenge` already contains, within its boundaries, a subject concord, a tense marker, a verb root, and (potentially) an object concord. To treat such a token as atomic is to inherit the analytical defaults of NLP traditions designed for European languages.

英語とアフリカーンス語にとっては、空白で区切られた語が機能的な分析単位である。しかし、isiZulu・isiXhosa・Sesotho・Setswana を含む本プロジェクトの対象バントゥ諸語にとっては、そうではない。`Ngithenge` のようなトークンは、その境界内にすでに主語一致、時制マーカー、動詞語幹、（場合により）目的語一致を含んでいる。このトークンを原子的に扱うことは、ヨーロッパ諸語のために設計された NLP の分析的デフォルトを無批判に継承することである。

### 2. Surface ML/EL labelling without morphology underdetermines what is happening in the data

Tagging a sentence as "Matrix Language = isiZulu, Embedded Language = English" tells us almost nothing about whether the English material is morphologically integrated, syntactically inserted, or freely alternated. Myers-Scotton's (1993, 2002) Matrix Language Frame model is precisely an instrument for distinguishing these cases, and it requires morpheme-level evidence.

文を「Matrix Language = isiZulu、Embedded Language = English」とタグ付けしても、英語要素が形態的に統合されているのか、統語的に挿入されているのか、自由に交替しているのか、ほとんど何も語らない。Myers-Scotton (1993, 2002) の Matrix Language Frame モデルは、まさにこれらの場合を区別するための装置であり、形態素レベルの証拠を必要とする。

### 3. The 4-M model is the minimum interpretive infrastructure

Surface morpheme classification (content, early system, bridge late system, outsider late system) is not a theoretical preference. It is the minimum infrastructure required to **test** claims made under MLF, rather than to merely **assert** them. Imbizo-CS does not force MLF onto researchers, but where MLF is invoked, the 4-M annotation layer is what makes the claim falsifiable.

表層の形態素分類（content・early system・bridge late system・outsider late system）は、理論的な好みではない。MLF の下で行われる主張を **単に断言する** のではなく **検証する** ために必要な最小限のインフラである。Imbizo-CS は MLF を研究者に強制しないが、MLF が呼び出される場面では、4-M アノテーション層が主張を反証可能にする。

When Imbizo-CS exports outward to LIDES, the exporter writes a companion losses file documenting which morphology-rich fields cannot travel cleanly. Loss documentation is part of the morphology commitment, not a footnote.

Imbizo-CS が LIDES へ外部出力するとき、exporter は形態論的に豊かなフィールドのうち何が完全には移送できないかを companion losses file に記録する。損失の記録は形態論への誓約の一部であり、脚注ではない。

### 4. The integration score is exposed and editable

The borrowing-integration score is not a number to be trusted; it is a weighted sum whose weights the researcher can inspect and edit per project. The researcher's theoretical position — whether they hold Poplack's (1980) strict borrowing/codeswitching distinction, or Muysken's (2000) continuum view — is not the software's to decide. The formula is transparent precisely so that disagreement with it can be a methodological choice, not a technical defeat.

借用統合スコアは信頼されるべき数値ではない。それは重み付き和であり、研究者は重みをプロジェクトごとに閲覧・編集できる。研究者の理論的立場 — Poplack (1980) の厳格な borrowing/code-switching 区別を採るのか、Muysken (2000) の連続体的見方を採るのか — は、ソフトウェアが決めるべきことではない。式が透明であるのは、それへの異議が技術的敗北ではなく方法論的選択でありうるためである。

### 5. Future contributors are warned

Do not silently improve "accuracy" by hard-coding a theoretical assumption. If you discover that adopting one particular MLF variant yields better numbers on a benchmark, that is not by itself a reason to embed that variant as the default. Imbizo-CS exists to **make theoretical disagreements visible**, not to absorb them into a hidden default.

ある特定の MLF 派生を採用すればベンチマーク上の数値が良くなることを発見したとして、それ自体はその派生をデフォルトに埋め込む理由にはならない。Imbizo-CS は理論的不一致を **不可視化する** のではなく **可視化する** ために存在する。

---

## Part III — Pluralism and refusal
## 第III部 — 多元性と拒否

### 1. v1.5 deliberately makes room for multiple theoretical traditions

The features introduced in v1.5 — sister-language disambiguator, triggered-switching detector, mixed-code variety mode, phonological integration scoring, LIDES / CHAT-CLAN interoperability, community review workflow — were not chosen because they fit any single theoretical school. They were chosen because each is necessary for at least one tradition of code-switching research, and because forcing a researcher to choose between traditions would itself be a methodological imposition.

v1.5 で導入された機能群（同系統言語弁別器、triggered switching 検出器、混合語体モード、音韻統合スコア、LIDES / CHAT-CLAN 相互運用、コミュニティレビュー workflow）は、いずれかの単一の理論学派に適合するから選ばれたのではない。それぞれが、コードスイッチング研究の少なくとも一つの伝統にとって必要だから選ばれた。そして、研究者に伝統間の選択を強制することは、それ自体が方法論的強制だからである。

### 2. Why the software refuses to declare a span as Tsotsitaal without researcher confirmation

Tsotsitaal, Iscamtho, Kaaps, Sabela are living urban varieties whose names, boundaries, and social meanings are themselves contested. To allow the software to silently label a span as "Tsotsitaal" on the basis of lexical density would be to **reify** a variety that is, in practice, defined relationally, performatively, and contextually. The detector reports lexical evidence; it never declares variety identity. Identity is the researcher's call, made with attention to speaker, setting, and history.

Tsotsitaal、Iscamtho、Kaaps、Sabela は生きている都市変種であり、その名前・境界・社会的意味自体が争われている。語彙密度に基づいてソフトウェアがスパンを「Tsotsitaal」と静かにラベル付けすることを許せば、それは実践においては関係的・パフォーマティブ・文脈的に定義される変種を **物象化** することになる。検出器は語彙的証拠を報告するが、変種同定を宣言することは決してない。同定は研究者の判断であり、話者・場面・歴史への注意とともに下される。

The sister-language disambiguator follows the same rule: it returns confidence and evidence, never declarations. Weak evidence preserves disagreement instead of hiding it behind a label.

同系統言語弁別器も同じ規則に従う。それは信頼度と証拠を返すが、宣言は返さない。弱い証拠は、不一致をラベルの背後に隠すのではなく保存する。

### 3. Why community-review packets queue rather than auto-apply

A USB-shared review packet from another researcher is not authoritative simply because it arrived. The software queues incoming packets as `pending`, displays their human-readable diffs, and requires the project owner's explicit action to apply, reject, or defer them. This is slower than auto-merge. It is supposed to be slower. **Disagreement preservation is a feature, not a bug.**

別の研究者から USB 経由で届いたレビューパケットは、到着したというだけで権威を持つものではない。ソフトウェアは入ってきたパケットを `pending` として queue し、人間可読の diff を表示し、プロジェクト所有者の明示的な行動（適用・却下・延期）を要求する。これは自動マージより遅い。**遅いことは欠陥ではなく機能である。不一致の保存は欠陥ではなく機能である。**

### 4. A pledge

Features that "improve accuracy" by hard-coding a single theoretical position are a regression in this project, regardless of their numerical performance.

単一の理論的立場をハードコードすることで「精度を改善する」機能は、その数値的性能に関わらず、本プロジェクトにおいては退化である。

---

## Part IV — Licence philosophy
## 第IV部 — ライセンス哲学

### 1. Licences are not technical details; they are political postures

Imbizo-CS handles code-switching, which is itself a politically entangled phenomenon — colonial history, racial politics, working-class linguistic practice, the language sovereignty of indigenous communities. The choice of licence for software that handles it cannot be neutral. Our licence structure is our answer to the following questions:

ライセンスは技術的詳細ではなく政治的姿勢の表明である。Imbizo-CS が扱うコードスイッチングは、植民地史・人種政治・労働階級の言語実践・先住民共同体の言語主権と絡み合った政治的現象である。それを扱うソフトのライセンス選択は中立ではあり得ない。我々のライセンス構造は次の問いへの回答である:

- How freely can a researcher using this software share their findings?
  このソフトを使う研究者は、自分の研究成果をどこまで自由に共有できるか
- What forms of respect do the data creators expect for their labour?
  データ作成者は自分たちの労力に対してどのような尊重を期待しているか
- How does the global-North digital humanities' default "openness" connect to African research communities' alternative openness?
  グローバルノースの DH のデフォルトな「オープン性」は、アフリカの研究共同体が提案する別のオープン性とどう接続するか

### 2. The three tiers

**Tier 1 — Core.** Resources fully compatible with AGPLv3 and with no commercial-use restriction. Default install. Downstream users can publish in any form, including commercial.

**Tier 1 — コア。** AGPLv3 と完全互換、商業利用制限なし。デフォルトインストール。下流ユーザーはどのような形式でも公開でき、商業利用も自由。

**Tier 2 — Optional NC.** Resources with NonCommercial or non-trivial compatibility constraints. Explicit opt-in only. At install time the user reads the obligations and confirms via environment variable. This is not designed to inconvenience; it is designed to **make "accepting without reading" structurally impossible**.

**Tier 2 — オプション NC。** 非商用または非互換制約を持つリソース。明示的オプトインのみ。インストール時に利用者は義務を読み、環境変数で確認意思を表明する。不便にするためではなく、**「読まずに承諾する」状態を構造的に不可能にする** ためである。

**Tier 3 — Community.** Resources licensed under sovereignty-aware frameworks developed by African communities themselves (e.g. NOODL). Never auto-downloaded; only routed through community-review packets. The choice is technical implementation of the choice **to honour licences that prioritise substantive fairness over formal equality**.

**Tier 3 — コミュニティ。** アフリカの共同体自身が策定した主権配慮型フレームワーク（NOODL 等）の下のリソース。自動ダウンロードされず、コミュニティレビューパケット経由のみ。これは **形式的平等よりも実質的公正を優先するライセンスを尊重する** 選択の技術的実装である。

### 3. Why we do not silently bundle CC-BY-NC data

Technically lawful. Ethically refused. The Masakhane community chose CC-BY-NC for MasakhaPOS / MasakhaNER as a deliberate decision against extractive commercial exploitation. Routing around that decision technically would not honour their intent. Researchers using this tool deserve to know **from the start**, not after a thesis is in press.

技術的には合法。倫理的に拒否する。Masakhane コミュニティが MasakhaPOS / MasakhaNER に CC-BY-NC を選んだのは、搾取的商業利用への意図的な決定である。それを技術的に迂回することは彼らの意思を尊重することではない。このツールを使う研究者は、博論が印刷に回された後ではなく、**最初から知る権利がある**。

### 4. Why we warn but do not block

The Tier-2 notification is dismissible. We do not treat researchers as children. But the licence notice **automatically propagates to the footer** of every exported report. The propagation is not to protect the researcher; it is to honour the readers, reviewers, and future researchers who will encounter the work.

Tier 2 通知は閉じることができる。研究者を子ども扱いしない。しかしライセンス通知はエクスポートされるすべてのレポートのフッターに **自動的に伝播する**。伝播は研究者を保護するためではなく、その成果を受け取る読者・査読者・将来の研究者を尊重するためである。

Static visualisation outputs, including heatmaps and Sankey diagrams, draw their licence-propagation footer from the same registry so figures do not silently detach from resource obligations.

ヒートマップや Sankey 図を含む静的な可視化出力も、同じ registry からライセンス伝播フッターを取得する。図がリソース義務から静かに切り離されることはない。

### 5. Why our software licence is AGPLv3

We choose AGPLv3 over GPLv3 because:

GPLv3 ではなく AGPLv3 を選ぶ理由:

- **SaaS-capture defence.** If a third party hosts Imbizo-CS as cloud SaaS, GPLv3 would not require source disclosure; AGPLv3 does.
  SaaS による囲い込みからの防衛。第三者が Imbizo-CS をクラウド SaaS としてホストする場合、GPLv3 ではソース公開義務が発生しないが、AGPLv3 では発生する。

- **Consistency with data sovereignty.** "Data stays with the user" must translate to "code stays with users even when offered as service." Same philosophy, different layer.
  データ主権との一貫性。「データは利用者の手元にある」は、「サービスとして提供される場合でもコードは利用者のものである」に翻訳されなければならない。同じ哲学、異なる層。

- **Protection for African researchers.** Our imagined user is an independent researcher with intermittent connectivity, not a SaaS company. AGPLv3 protects against a future where someone re-sells this software back as a hosted service.
  アフリカ研究者の保護。我々が想定する利用者は SaaS 企業ではなく、断続的接続で研究する独立研究者である。AGPLv3 は、このソフトが誰かによってホスト型サービスとして売り戻される未来からの防衛である。

### 6. Our stance on NOODL

The Nwulite Obodo Open Data License is a new open data licence drafted by **African data communities themselves**. Its tripartite structure (Licensor / Licensees from developing nations / Licensees from developed nations) represents a decisive philosophical turn from "formal equality" to "substantive fairness".

Nwulite Obodo Open Data License は、**アフリカのデータ共同体自身** によって策定された新しいオープンデータライセンスである。その三者構造（Licensor / Licensees from developing nations / Licensees from developed nations）は、「形式的平等」から「実質的公正」への決定的な哲学的転換を表している。

Imbizo-CS recognises NOODL — regardless of its current technical maturity — as a pioneering experiment that future digital-humanities licensing design should learn from. We route NOODL resources through Tier 3 not as a compromise but as an attempt to **translate NOODL's spirit into our technical implementation**.

Imbizo-CS は NOODL を、現在の技術的成熟度に関わらず、未来の DH ライセンス設計が学ぶべき先進的実験として認める。NOODL リソースを Tier 3 に振り分けるのは妥協ではなく、**NOODL の精神を技術的実装に翻訳する** 試みである。

In the longer term we aspire to dialogue with Masakhane and DSFSI about re-licensing portions of their datasets under NOODL or CC-BY-4.0. This is a political project, not a technical one.

長期的には、Masakhane や DSFSI と、彼らのデータセットの一部を NOODL や CC-BY-4.0 で再ライセンスする可能性について対話したい。これは政治的プロジェクトであり、技術的決定ではない。

---

## Part V — The political economy of research software
## 第V部 — 研究ソフトウェアの政治経済学

### 1. Why offline-first is not nostalgia

Cloud-default software design treats reliable internet, cheap electricity, persistent storage, and corporate-grade authentication as background conditions. For a significant share of the world's researchers — including most of those who would naturally study South African code-switching — none of these conditions hold by default. Offline-first is therefore not a retrospective concession to "less privileged users"; it is a methodological commitment to **not import the infrastructural assumptions of global-North research into a context where they were never warranted**.

クラウドをデフォルトとするソフト設計は、信頼できるインターネット、安価な電力、永続的なストレージ、企業グレードの認証を背景条件として扱う。世界の研究者の相当部分にとって — 南アフリカのコードスイッチングを自然に研究する大半の人々を含む — これらの条件はデフォルトでは成立しない。したがってオフライン・ファーストは、「特権の少ない利用者」への遡及的譲歩ではない。それは **グローバルノースの研究のインフラ的前提を、それが正当化されたことのない文脈に持ち込まない** という方法論的誓約である。

All visualisations render offline with matplotlib and embed SVG text as paths, so sharing a figure does not depend on a recipient having matching fonts, network access, or a web plotting service.

すべての可視化は matplotlib によりオフラインで描画され、SVG ではテキストを path として埋め込む。図の共有は、受信者が同じフォント・ネットワーク接続・Web プロットサービスを持つことに依存しない。

### 2. Why automation is auxiliary, not authoritative

The history of NLP-assisted humanities scholarship is, in significant part, a history of automatic outputs becoming citable claims through institutional inertia. We refuse this. Every automatic decision in Imbizo-CS carries an `auto` badge, is overridable, and is logged with provenance. The point is not to reduce automation; it is to ensure that **the researcher's interpretive labour remains the locus of authority**, and that this labour is documented rather than effaced.

NLP 支援の人文学研究の歴史は、相当部分、自動出力が制度的慣性によって引用可能な主張になっていく歴史である。我々はこれを拒否する。Imbizo-CS におけるすべての自動判定は `auto` バッジを付け、上書き可能で、provenance とともに記録される。自動化を減らすことが目的ではない。**研究者の解釈労働こそが権威の所在であり、その労働が消去されるのではなく文書化される** ことを保証するためである。

### 3. Why Bantu morphology cannot be reduced to whitespace tokenisation

(See Part II.) Reiterated here because future contributors will be tempted, repeatedly, to use whitespace tokenisers for "simplicity". The simplicity is borrowed from a typology that does not fit. Borrowing it would not be simplicity; it would be **simplification through erasure**.

（第II部参照。）ここで再掲する理由は、将来の貢献者が「単純さ」のために空白トークナイザーを使いたい誘惑に繰り返し駆られるからである。その単純さは適合しない類型論から借りてきたものである。それを借りることは単純さではなく、**消去による単純化** である。

### 4. Why we refuse cloud LLM dependencies by default, while leaving a plug-in door open

Cloud-hosted large language models are powerful. They are also: expensive at scale, dependent on persistent connectivity, opaque about training data provenance, governed by corporate terms that can change without notice, and structurally biased toward the languages and registers their training data over-represented. To depend on them by default is to import all of these properties into a project whose entire purpose is to **make a different kind of dependency possible**.

クラウドホストの大規模言語モデルは強力である。同時にそれは、スケールで高価であり、永続的接続に依存し、訓練データの provenance について不透明であり、予告なく変更されうる企業条項に支配され、訓練データが過剰代表する言語・レジスターに構造的にバイアスがかかっている。これらをデフォルトで依存することは、**異なる種類の依存関係を可能にする** ことを全目的とするプロジェクトに、これらの性質をすべて持ち込むことである。

We leave a plug-in door open because we refuse paternalism: a researcher who has read the trade-offs and chooses LLM augmentation for their context is exercising informed judgement, not making an error. But the door is opt-in, gated, and documented, not a default.

我々はパターナリズムを拒否するため、プラグインの扉は開けたままにする。トレードオフを読んだ上で自分の文脈で LLM 補強を選ぶ研究者は、誤りを犯しているのではなく、informed judgement を行使している。しかし扉はオプトインで、ゲーティングされ、文書化されており、デフォルトではない。

### 5. Connections to broader frameworks

This document, and the software it governs, draws on and aspires to align with:

本文書、およびそれが統治するソフトウェアは、以下の枠組みに依拠し、それらとの整合を目指す:

- **Indigenous Data Sovereignty** and the **CARE Principles for Indigenous Data Governance** (Carroll et al., 2020).
  先住民データ主権と先住民データガバナンスのための CARE 原則。

- **Decolonial computing** (Ali, 2016) and **postcolonial digital humanities** (Risam, 2018).
  脱植民地コンピューティングとポストコロニアル・デジタル人文学。

- **FAIR4RS principles** for research software (Chue Hong et al., 2022) and **FORCE11 software-citation principles** (Smith et al., 2016) — adopted where they are compatible with the above, and contested where they presume infrastructure we reject.
  研究ソフトのための FAIR4RS 原則と FORCE11 ソフトウェア引用原則 — 上記と互換である限り採用し、我々が拒否するインフラを前提とする場面では争点化する。

- **Free Software Foundation** licensing philosophy, **Creative Commons** licence compatibility guidance, and the **Nwulite Obodo Open Data License** as a community-rooted alternative.
  FSF のライセンス哲学、Creative Commons の互換性ガイダンス、そしてコミュニティ根差しの代替としての NOODL。

---

## Part VI — A pledge to future contributors
## 第VI部 — 将来の貢献者への誓い

### 1. Erosion is regression

Future contributors may propose:

将来の貢献者は次のように提案するかもしれない:

- "Cloud sync would just be optional, why not add it?"
  「クラウド同期はオプションにすぎない、なぜ加えないのか？」

- "Removing the NC warning would improve UX."
  「NC 警告を削除すれば UX が改善する」

- "Including Tier-2 by default would simplify installation."
  「Tier 2 をデフォルトに含めればインストールが簡略化される」

- "Dropping the licence notice from report footers would make outputs cleaner."
  「ライセンス通知をレポートフッターから外せば出力が綺麗になる」

- "NOODL is technically immature; collapse Tier 3 into Tier 1 or Tier 2."
  「NOODL は技術的に未成熟、Tier 3 を Tier 1 か 2 に統合しよう」

- "A small LLM dependency would solve many edge cases."
  「小さな LLM 依存があれば多くのエッジケースが解決する」

- "Why not auto-merge community review packets to reduce friction?"
  「摩擦を減らすためコミュニティレビューパケットを自動マージすれば？」

- "Whitespace tokenisation is faster and would let us ship a basic Bantu mode."
  「空白トークン化のほうが速い、基本的なバントゥモードを出荷できる」

Each of these is a **regression**, not an improvement. Each erodes a principle that this project exists to defend.

これらのいずれも **改善ではなく退化** である。各提案は本プロジェクトが擁護するために存在する原則を侵食する。

### 2. The change process

If a future contributor wishes to change a principle stated in this document, the change must:

将来の貢献者が本文書に述べられた原則を変更したい場合、その変更は:

1. Be proposed first as a revision to PRINCIPLES.md, not as a code PR.
   まずコード PR としてではなく、PRINCIPLES.md の改訂提案として行わなければならない。

2. Include a written argument addressing **why** the principle as stated is mistaken.
   述べられた原則がなぜ誤りであるかについての文章による議論を含まなければならない。

3. Address how the change preserves — or explicitly redefines — the relationship with the communities whose data and labour this project depends on.
   その変更が、本プロジェクトが依拠するデータと労働の共同体との関係をどのように保存するか、あるいは明示的に再定義するかを論じなければならない。

4. Be reviewed by at least one contributor with sustained engagement in a South African Bantu language community, where the change touches Bantu-language handling.
   バントゥ諸語の扱いに関わる変更の場合、南アフリカのバントゥ言語共同体と持続的な関わりを持つ貢献者の少なくとも一人によるレビューを経なければならない。

5. Be reviewed by at least one contributor with sustained engagement in offline / low-resource research contexts, where the change touches infrastructure assumptions.
   インフラ前提に関わる変更の場合、オフライン・低資源研究の文脈と持続的な関わりを持つ貢献者の少なくとも一人によるレビューを経なければならない。

### 3. Why this matters

This software exists to make a small contribution to the larger project of **decolonising research infrastructure**. That contribution is meaningful only as long as the principles stated here are defended **not as preferences, but as constitutive commitments**. To erode them quietly through code is contrary to the spirit of this project.

このソフトウェアは、**研究インフラを脱植民地化する** という大きなプロジェクトへの小さな貢献として存在する。その貢献は、ここに述べられた原則が **好みとしてではなく構成的誓約として** 擁護される限りにおいてのみ意味を持つ。コードを通じて静かに侵食することは、本プロジェクトの精神に反する行為である。

---

## Appendix — References cited in this document
## 付録 — 本文書で引用された文献

- Ali, S. M. (2016). A brief introduction to decolonial computing. *XRDS: Crossroads*, 22(4), 16–21.
- Carroll, S. R., Garba, I., Figueroa-Rodríguez, O. L., Holbrook, J., Lovett, R., Materechera, S., et al. (2020). The CARE Principles for Indigenous Data Governance. *Data Science Journal*, 19(1), 43.
- Chue Hong, N. P., et al. (2022). *FAIR Principles for Research Software (FAIR4RS Principles)*. Research Data Alliance.
- Creative Commons. (n.d.). *Compatible Licenses*. https://creativecommons.org/compatible-licenses/
- Free Software Foundation. (2007). *GNU Affero General Public License version 3*. https://www.gnu.org/licenses/agpl-3.0.html
- Free Software Foundation. (2021). *The fundamentals of the AGPLv3*. https://www.fsf.org/bulletin/2021/fall/the-fundamentals-of-the-agplv3
- Muysken, P. (2000). *Bilingual speech: A typology of code-mixing*. Cambridge University Press.
- Myers-Scotton, C. (1993). *Duelling languages: Grammatical structure in codeswitching*. Oxford University Press.
- Myers-Scotton, C. (2002). *Contact linguistics: Bilingual encounters and grammatical outcomes*. Oxford University Press.
- Okorie, C., et al. (2024). *Nwulite Obodo Open Data License version 1.0*. Data Science Law Lab. https://licensingafricandatasets.com/nwulite-obodo-license
- Poplack, S. (1980). Sometimes I'll start a sentence in Spanish y termino en español. *Linguistics*, 18(7/8), 581–618.
- Risam, R. (2018). *New digital worlds: Postcolonial digital humanities in theory, praxis, and pedagogy*. Northwestern University Press.
- Smith, A. M., Katz, D. S., Niemeyer, K. E., & FORCE11 Software Citation Working Group. (2016). Software citation principles. *PeerJ Computer Science*, 2:e86.

---

## Closing — 結語

This document is signed by no individual. It is signed, prospectively, by every researcher who chooses to use, modify, or contribute to Imbizo-CS Workbench. To use this software is to engage with these principles. To contribute to it is to defend them. To fork it under a different name and discard these principles is permissible; to fork it under this name and discard these principles is not.

本文書はいかなる個人によっても署名されていない。それは、Imbizo-CS Workbench を使用・修正・貢献することを選ぶすべての研究者によって、未来に向けて署名される。このソフトを使うことは、これらの原則と関わることである。貢献することは、それらを擁護することである。異なる名前でフォークしてこれらの原則を捨てることは許される。同じ名前でフォークしてこれらの原則を捨てることは許されない。

— The Imbizo-CS Workbench Project
— Imbizo-CS Workbench プロジェクト

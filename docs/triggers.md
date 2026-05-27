# Triggered Switching in Imbizo-CS v1.5

Triggered switching is one way of asking why a switch appears where it does.
Michael Clyne proposed that some words or expressions can help create a local
environment in which a speaker moves from one language into another (Clyne, 1967, 2003). The trigger may be a proper noun, a borrowed term, a cognate, a
repeated form, or a discourse marker that belongs partly to more than one
linguistic system. Imbizo-CS v1.5 gives this idea first-class support, but it
does so cautiously. A trigger candidate is evidence for interpretation. It is
not proof of the speaker's reason.

## The Basic Idea

Imagine a multilingual interview where a speaker is mostly using isiZulu but
mentions a workplace term in English, then continues in English for the next
clause. A Clyne-style analysis asks whether the workplace term helped create the
switching point. This is different from simply saying "the Matrix Language is
isiZulu" or "the Embedded Language is English." Matrix Language analysis focuses
on the grammatical frame of the utterance, while triggering focuses on local
sequential cues near a switch boundary (Clyne, 2003; Myers-Scotton, 1993).

Conversation analysts also remind us that code-switching is embedded in turn
design, repair, stance, quotation, and audience orientation (Auer, 1998).
Therefore, Imbizo-CS does not treat trigger detection as a causal explanation.
The software scans a small window before a switch point and asks: "Is there a
known kind of trigger candidate here?" It then asks the researcher to confirm,
reject, or annotate the candidate in context.

## Common South African Trigger Types

The following examples are paraphrased and simplified. They are for learning the
interface, not for publication without project-specific verification.

Proper nouns (paraphrased example): A speaker names a school, church, company,
political office, or city whose conventional name is in English or Afrikaans,
then continues briefly in that language. The name may function as a local bridge
between languages. In Imbizo-CS, a proper noun can be marked as a candidate
trigger, but the speaker's reason must be interpreted from the interaction.

Technology borrowings (paraphrased example): Words such as `laptop`, `Wi-Fi`,
`WhatsApp`, or `email` often circulate across languages. A technology term may
appear inside a Bantu grammatical frame, or it may cue a shift into an English
technical register. v1.5 dictionaries list some domain terms as trigger
candidates, with `verified: false` where the list is only a starter set.

Religious vocabulary (paraphrased example): Church interviews may include terms
such as `pastor`, `service`, `prayer`, or denominational names. In some contexts
these are deeply integrated local terms; in others, they may invite a switch to
English, Afrikaans, or another language. The trigger panel records the candidate
status without deciding meaning.

Governance and education terms (paraphrased example): Terms such as `municipal`,
`department`, `principal`, `policy`, or `application` may carry institutional
language histories. The software can flag them as possible triggers, but the
researcher must decide whether the term is relevant to the switch or merely
co-occurs with it.

Discourse markers (paraphrased example): Words like `so`, `okay`, `mos`, or
other local markers may sit at boundaries between discourse moves. Some may
trigger or accompany a language shift. Because these forms can be highly
contextual, the dictionary entries are deliberately editable.

## How the Detector Works

When the annotation editor identifies a switch boundary, the trigger tool scans
the previous one to three tokens. It compares those tokens against local trigger
dictionaries for the active languages. Matches are ranked by transparent rules:
proper nouns and dictionary-marked trigger words count as stronger candidates
than weak context matches; closer tokens count more than distant ones; manual
confirmations always outrank suggestions.

The detector never writes a final trigger link by itself. A candidate appears
with a visible suggestion marker. Right-clicking the candidate lets the
researcher choose "Confirm trigger" or "Reject suggestion." A confirmed link is
saved in the `trigger_links` table and recorded in provenance. A rejected link
can also be recorded, because rejected evidence can matter in a methods section.

## Reading the Trigger Profile Report

The Trigger Profile report summarizes confirmed triggers by speaker, scene, time
range, and trigger type. It can show, for example, whether technology terms are
frequent switch-adjacent candidates in workplace interviews, or whether proper
nouns appear near switches in religious narratives. The timeline view shows
trigger density across the interview, helping researchers locate clusters for
closer qualitative reading.

Do not read the report as a map of intentions. It counts confirmed analytic
links. It does not prove that a speaker switched because of a particular word.
For writing, prefer cautious phrasing such as "the switch is associated with a
confirmed trigger candidate" rather than "the word caused the switch." This is
especially important when studying sensitive topics, identity, education, or
institutional power.

## Avoiding Post-Hoc Rationalization

Triggered-switching analysis is attractive because it gives pattern to messy
data. That is also its danger. Once a switch is visible, it is easy to search
backward and find a word that seems to explain it. Imbizo-CS reduces this risk
by making candidates explicit, local, and reviewable. The dictionary entry,
window size, confidence, confirmation status, and researcher memo are all saved.
The researcher can also report negative cases: switch boundaries where no
candidate was found, or where a candidate was rejected.

Good practice is to use trigger evidence alongside other analyses: Matrix
Language structure, turn-taking, participant role, topic, genre, and local
ethnographic knowledge (Auer, 1998; Myers-Scotton, 1993). Triggering is one lens
among several. It should sharpen interpretation, not replace it.

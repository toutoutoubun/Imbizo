# Optional ASR Quality Disclaimer

Imbizo-CS does not bundle ASR as a default feature. Manual transcription remains
the default because qualitative interview analysis depends on accountable,
auditable listening.

The optional whisper.cpp bootstrap path exists for researchers who knowingly
choose to experiment with local ASR. It requires `--include-asr` and
`IMBIZO_ASR_ACCEPTED=1`. This is deliberate friction. Whisper's accuracy on
isiZulu, isiXhosa, Sesotho, Setswana, and multilingual South African interview
speech is unknown or likely uneven. South African code-switching ASR has known
resource and accuracy constraints (Yilmaz et al., 2018), and 2024 reporting on
AI transcription tools documented fabricated text and high-risk errors in
Whisper-based workflows (Associated Press, 2024).

Use ASR output only as a rough draft. Always listen back, correct the transcript,
and record that machine assistance was used. Never treat ASR text as
authoritative evidence of what a participant said.

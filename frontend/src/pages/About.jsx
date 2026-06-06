import { useState } from "react"
import Footer from "../components/Footer"

const GITHUB = "https://github.com/SujayKulkarni-2211/SankaRAGamana"

export default function About() {
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1 w-full" style={{ maxWidth: "var(--measure)", margin: "0 auto", padding: "var(--space-2xl) var(--space-md)" }}>
        {/* Header */}
        <p className="mono" style={{ fontSize: ".68rem", letterSpacing: ".16em", textTransform: "uppercase", color: "var(--ink-faint)", marginBottom: "var(--space-sm)" }}>
          colophon
        </p>
        <h1 className="display" style={{ fontSize: "2.6rem", fontWeight: 500, color: "var(--ink)", lineHeight: 1.1, marginBottom: "var(--space-xs)", letterSpacing: "-.015em" }}>
          Sanka<span style={{ color: "var(--flame)" }}>RĀG</span>amana
        </h1>
        <p className="deva" style={{ color: "var(--flame)", fontSize: "1.5rem", marginBottom: "var(--space-xl)" }}>
          अथातो ब्रह्म जिज्ञासा
        </p>

        <Section title="What this is">
          <p>
            SankaRĀGamana uses RAG (Retrieval Augmented Generation) to retrieve
            Śaṅkarācārya's own words from his texts and present them in response
            to your inquiry. The name encodes this:{" "}
            <em>Śaṅkara + RĀG + Āgamana</em> — the coming of Śaṅkara through
            retrieval.
          </p>
        </Section>

        {/* ── Under the hood: collapsible technical sections ── */}
        <section style={{ marginBottom: "var(--space-xl)" }}>
          <h2 className="mono" style={{ fontSize: ".72rem", letterSpacing: ".14em", textTransform: "uppercase", color: "var(--flame)", marginBottom: "var(--space-md)" }}>
            Under the hood
          </h2>
          <p style={{ color: "var(--ink-soft)", marginBottom: "var(--space-md)", fontSize: "1.02rem", lineHeight: 1.75 }}>
            This is not a single model answering from memory. It is a small
            agreement of parts, each doing one honest thing. Open any layer.
          </p>

          <Tech n="01" title="Two minds, one in Sanskrit">
            Your question is translated into classical Sanskrit and embedded
            against a corpus that is itself Sanskrit — so retrieval happens in
            the language the texts actually live in, where meaning lands closest.
            A second path keeps your own language, because today's models explain
            in English more clearly than they reason in Sanskrit. The Sanskrit
            path is the spine; the language path is the clarifying hand.
          </Tech>

          <Tech n="02" title="Retrieval that knows when a book is truly about something">
            Every one of the ~4,100 passages is embedded. But raw similarity lets
            a large text flood the results by sheer volume. So each book also has
            a <em>centroid</em> — its average meaning. When one source dominates,
            we check the query against that centroid: is the book genuinely about
            this, or did it just have a few look-alike lines? Honest domination is
            allowed; lazy flooding is pushed aside so several works can speak.
          </Tech>

          <Tech n="03" title="A reflection that weaves, not a winner that copies">
            Both paths are audited on grounding, register, and coverage. Then a
            separate step composes the final teaching — taking the Sanskrit path's
            authentic verses and the language path's clarity, citing several
            sources, explaining each, and ending in how to live it. It may only
            quote verses that were actually retrieved; it never invents scripture.
          </Tech>

          <Tech n="04" title="The seeker, met where they are">
            Before any of this, a profiler reads not just your words but the
            shape of your question — its depth, its intent, whether it carries
            distress. That reading tunes how fully the answer unfolds, the way a
            teacher meets a beginner and a scholar differently with the same text.
          </Tech>
        </section>

        <Section title="The data">
          <p className="mb-3">The texts in this corpus are sourced from:</p>
          <ul className="space-y-2 ml-2">
            <li>
              <span className="text-[var(--saffron)]">·</span>{" "}
              <a
                href="https://sanskritdocuments.org"
                target="_blank"
                rel="noreferrer"
                className="underline decoration-dotted hover:text-[var(--saffron)] transition-colors"
              >
                sanskritdocuments.org
              </a>{" "}
              — Unicode Devanagari texts of Śaṅkara's prakaraṇa granthas and
              stotras
            </li>
            <li>
              <span className="text-[var(--saffron)]">·</span>{" "}
              <a
                href="https://gretil.sub.uni-goettingen.de"
                target="_blank"
                rel="noreferrer"
                className="underline decoration-dotted hover:text-[var(--saffron)] transition-colors"
              >
                GRETIL
              </a>{" "}
              — Göttingen Register of Electronic Texts in Indian Languages —
              machine-readable Sanskrit texts
            </li>
          </ul>
          <p className="mt-4 text-[var(--muted)]">
            We do not claim ownership of these teachings. These texts belong to
            the paramparā.
          </p>
        </Section>

        <Section title="Texts in the corpus">
          <p className="mb-4">
            The system retrieves from 32 of Śaṅkarācārya's works — over 4,000
            passages embedded for semantic search. The foundational Bhāṣyas form
            the doctrinal core; the prakaraṇa granthas and stotras give voice and
            accessibility.
          </p>

          <TextGroup title="Bhāṣya — Commentaries (the doctrinal core)">
            <TextItem dev="ब्रह्मसूत्रशाङ्करभाष्यम्" rom="Brahma Sūtra Bhāṣya" note="Śaṅkara's definitive statement on Advaita" />
            <TextItem dev="श्रीमद्भगवद्गीताशाङ्करभाष्यम्" rom="Bhagavad Gītā Bhāṣya" note="commentary on the Gītā" />
            <TextItem dev="केनोपनिषद्शाङ्करभाष्यम्" rom="Kena Upaniṣad Bhāṣya" />
            <TextItem dev="ईशावास्योपनिषद्शाङ्करभाष्यम्" rom="Īśāvāsya Upaniṣad Bhāṣya" />
          </TextGroup>

          <TextGroup title="Prakaraṇa Granthas — Independent treatises">
            <TextItem dev="विवेकचूडामणिः" rom="Vivekacūḍāmaṇi" />
            <TextItem dev="उपदेशसाहस्री" rom="Upadeśasāhasrī" />
            <TextItem dev="अपरोक्षानुभूतिः" rom="Aparokṣānubhūti" />
            <TextItem dev="तत्त्वबोधः" rom="Tattvabodha" />
            <TextItem dev="आत्मबोधः" rom="Ātmabodha" />
            <TextItem dev="पञ्चीकरणम्" rom="Pañcīkaraṇam" />
            <TextItem dev="वाक्यवृत्तिः" rom="Vākyavṛtti" />
            <TextItem dev="दृग्दृश्यविवेकः" rom="Dṛg-Dṛśya-Viveka" />
            <TextItem dev="तत्त्वोपदेशः" rom="Tattvopadeśa" />
            <TextItem dev="अद्वैतानुभूतिः" rom="Advaitānubhūti" />
            <TextItem dev="प्रश्नोत्तररत्नमालिका" rom="Praśnottara-ratnamālikā" />
            <TextItem dev="ब्रह्मज्ञानावलीमाला" rom="Brahmajñānāvalīmālā" />
            <TextItem dev="लघुवाक्यवृत्तिः" rom="Laghu-Vākyavṛtti" />
            <TextItem dev="मायापञ्चकम्" rom="Māyā-Pañcakam" />
            <TextItem dev="साधनपञ्चकम्" rom="Sādhana-Pañcakam" />
            <TextItem dev="स्वरूपानुसन्धानाष्टकम्" rom="Svarūpa-anusandhāna-aṣṭakam" />
            <TextItem dev="दशश्लोकी" rom="Daśaślokī" />
            <TextItem dev="एकश्लोकी" rom="Ekaślokī" />
            <TextItem dev="यतिपञ्चकम्" rom="Yati-Pañcakam" />
            <TextItem dev="कौपीनपञ्चकम्" rom="Kaupīna-Pañcakam" />
          </TextGroup>

          <TextGroup title="Stotras — Hymns of devotion">
            <TextItem dev="भजगोविन्दम्" rom="Bhaja Govindam" />
            <TextItem dev="गणेशपञ्चरत्नम्" rom="Gaṇeśa-Pañcaratnam" />
            <TextItem dev="दक्षिणामूर्तिस्तोत्रम्" rom="Dakṣiṇāmūrti Stotram" />
            <TextItem dev="कालभैरवाष्टकम्" rom="Kālabhairava-Aṣṭakam" />
            <TextItem dev="गुर्वष्टकम्" rom="Gurvaṣṭakam" />
            <TextItem dev="तोटकाष्टकम्" rom="Toṭakāṣṭakam" />
            <TextItem dev="काशीपञ्चकम्" rom="Kāśī-Pañcakam" />
            <TextItem dev="मनीषापञ्चकम्" rom="Manīṣā-Pañcakam" />
          </TextGroup>
        </Section>

        <Section title="On rate limits">
          <p className="mb-3">
            This service is offered freely as sevā. We do not monetize it. We do
            not intend to.
          </p>
          <p className="mb-3">
            Rate limits exist solely to keep the service available to all seekers
            equally. We do not have the means to run this at unlimited scale.
          </p>
          <p>
            If you wish to engage with these teachings without limits, the
            complete source code is available on{" "}
            <a
              href={GITHUB}
              target="_blank"
              rel="noreferrer"
              className="underline decoration-dotted hover:text-[var(--saffron)] transition-colors"
            >
              GitHub
            </a>
            . You are welcome to run your own instance.
          </p>
        </Section>

        <Section title="On accuracy">
          <p className="mb-3">
            This system retrieves Śaṅkarācārya's words and presents them. It
            does not interpret, adjudicate, or claim doctrinal authority.
          </p>
          <p className="mb-3">
            Every response cites its source. Every claim traces to a retrieved
            passage. When the corpus does not contain an answer, the system says
            so.
          </p>
          <p className="text-[var(--muted)]">
            The ultimate authority on these teachings rests with the living
            paramparā.
          </p>
        </Section>

        <Section title="Source code">
          <p className="mb-3">
            <a
              href={GITHUB}
              target="_blank"
              rel="noreferrer"
              className="text-[var(--saffron)] hover:underline break-all"
            >
              {GITHUB}
            </a>
          </p>
          <p className="text-[var(--muted)]">
            View source, report issues, run your own instance.
          </p>
        </Section>
      </main>
      <Footer />
    </div>
  )
}

function Section({ title, children }) {
  return (
    <section className="mb-10">
      <h2 className="mono" style={{ fontSize: ".72rem", letterSpacing: ".14em", textTransform: "uppercase", color: "var(--flame)", marginBottom: "var(--space-sm)" }}>
        {title}
      </h2>
      <div style={{ color: "var(--ink)", lineHeight: 1.75, fontSize: "1.05rem" }}>
        {children}
      </div>
    </section>
  )
}

// Collapsible technical layer — numbered, with a hairline that draws on open.
function Tech({ n, title, children }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ borderTop: "1px solid var(--rule)", padding: "var(--space-sm) 0" }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: "100%", display: "flex", alignItems: "baseline", gap: "var(--space-sm)",
          background: "none", border: "none", cursor: "pointer", textAlign: "left",
          padding: "var(--space-2xs) 0", fontFamily: "var(--font-body)",
        }}
      >
        <span className="mono" style={{ fontSize: ".74rem", color: "var(--flame)", flexShrink: 0 }}>{n}</span>
        <span className="display" style={{ flex: 1, fontSize: "1.12rem", color: "var(--ink)", fontWeight: 500, lineHeight: 1.35 }}>
          {title}
        </span>
        <span className="mono" style={{ fontSize: ".9rem", color: "var(--ink-faint)", flexShrink: 0, transition: "transform .3s var(--ease-ink)", transform: open ? "rotate(90deg)" : "none" }}>→</span>
      </button>
      <div style={{
        maxHeight: open ? 400 : 0, overflow: "hidden",
        transition: "max-height .4s var(--ease-ink), opacity .3s",
        opacity: open ? 1 : 0,
      }}>
        <p style={{
          padding: "var(--space-sm) 0 var(--space-xs)",
          paddingLeft: "calc(.74rem + var(--space-sm))",
          color: "var(--ink-soft)", lineHeight: 1.78, fontSize: "1rem",
        }}>
          {children}
        </p>
      </div>
    </div>
  )
}

function TextGroup({ title, children }) {
  return (
    <div className="mb-6">
      <h3 className="text-[var(--text2)] text-sm font-semibold mb-2">{title}</h3>
      <ul className="space-y-1.5">{children}</ul>
    </div>
  )
}

function TextItem({ dev, rom, note }) {
  return (
    <li className="flex flex-wrap items-baseline gap-x-2">
      <span
        className="font-['Noto_Sans_Devanagari'] text-[var(--text)]"
        style={{ fontSize: "1.05rem" }}
      >
        {dev}
      </span>
      <span className="text-[var(--muted)] text-[0.95rem]">{rom}</span>
      {note && (
        <span className="text-[var(--muted)] text-[0.85rem] italic">
          — {note}
        </span>
      )}
    </li>
  )
}

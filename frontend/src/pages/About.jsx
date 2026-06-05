import Footer from "../components/Footer"

const GITHUB = "https://github.com/SujayKulkarni-2211/SankaRAGamana"

export default function About() {
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1 max-w-2xl mx-auto px-4 py-12 w-full">
        {/* Header */}
        <h1 className="text-3xl font-semibold text-[var(--text)] mb-1">
          SankaRĀGamana
        </h1>
        <p className="text-[var(--saffron)] text-lg mb-10 font-['Noto_Sans_Devanagari']">
          अथातो ब्रह्म जिज्ञासा
        </p>

        <Section title="What this is">
          <p>
            SankaRĀGamana uses RAG (Retrieval Augmented Generation) techniques
            to retrieve Śaṅkarācārya's own words from his texts and present them
            in response to your inquiry. The name encodes this:{" "}
            <em>Sankara + RĀG + Āgamana</em> — the coming of Śaṅkara through
            retrieval.
          </p>
        </Section>

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
      <h2 className="text-[var(--saffron)] text-xs uppercase tracking-widest mb-3 font-sans">
        {title}
      </h2>
      <div className="text-[var(--text)] leading-relaxed space-y-2 text-[1.05rem]">
        {children}
      </div>
    </section>
  )
}

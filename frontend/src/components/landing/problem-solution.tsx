import { CheckCircle2, MinusCircle } from "lucide-react";

const painPoints = [
  "Lesson notes, videos, and homework scattered across chat groups and email threads.",
  "Grades tracked in disconnected spreadsheets with no clear draft-to-publish control.",
  "Parents left waiting until end of term to discover missing work or attendance issues.",
  "Weak boundaries when schools share generic tools without strict school-level access control.",
];

const klasraAnswers = [
  "Every lesson, video, file, assignment, quiz, and exam organized by academic year, term, and subject offering.",
  "Auto-graded quizzes and manual essay review with explicit publish controls before scores appear.",
  "Approved parents use one account across multiple schools to view only their own children's published progress.",
  "Server-enforced school isolation, private signed file URLs, and an audit trail on every sensitive action.",
];

export function ProblemSolution() {
  return (
    <section
      id="why-klasra"
      className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8"
    >
      <div className="max-w-2xl">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
          Why Klasra
        </p>
        <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-foreground">
          Built to replace fragmented classroom workflows.
        </h2>
        <p className="mt-3 text-base leading-relaxed text-muted-foreground">
          Secondary schools coordinate hundreds of students, multiple terms,
          specialized subjects, and families across campuses. Generic tools
          break down quickly.
        </p>
      </div>

      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border border-border bg-card p-6 sm:p-7">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            The Fragmented Reality
          </p>
          <ul className="mt-5 space-y-4">
            {painPoints.map((point) => (
              <li
                key={point}
                className="flex items-start gap-3 text-sm leading-relaxed text-muted-foreground"
              >
                <MinusCircle className="mt-0.5 h-4 w-4 shrink-0 text-zinc-400 dark:text-zinc-600" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-primary/25 bg-card p-6 sm:p-7 dark:border-primary/30">
          <p className="text-xs font-semibold uppercase tracking-wider text-primary">
            With Klasra
          </p>
          <ul className="mt-5 space-y-4">
            {klasraAnswers.map((point) => (
              <li
                key={point}
                className="flex items-start gap-3 text-sm leading-relaxed text-foreground"
              >
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

"use client";

const testimonials = [
  {
    quote:
      "Optimus a reduit notre temps de recherche de candidats de 70%. L'algorithme de matching est incroyablement precis.",
    author: "Marie Dupont",
    role: "Directrice RH, TechCorp",
    avatar: "MD",
  },
  {
    quote:
      "Enfin un outil qui comprend nos besoins. Les shortlists intelligentes nous font gagner des heures chaque semaine.",
    author: "Pierre Martin",
    role: "Consultant independant",
    avatar: "PM",
  },
  {
    quote:
      "La plateforme est intuitive et les analytics nous permettent de prendre des decisions data-driven. Indispensable.",
    author: "Sophie Bernard",
    role: "CEO, TalentAgency",
    avatar: "SB",
  },
];

export function Testimonials() {
  return (
    <section className="py-20 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-[color:var(--text-strong)] sm:text-4xl">
            Ils nous font confiance
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-[color:var(--text)]">
            Des centaines de professionnels utilisent Optimus pour optimiser leur staffing.
          </p>
        </div>
        
        <div className="mt-16 grid gap-8 md:grid-cols-3">
          {testimonials.map((testimonial) => (
            <div
              key={testimonial.author}
              className="rounded-2xl border border-black/10 bg-white p-8 shadow-sm"
            >
              <div className="flex items-center gap-1 text-yellow-400">
                {[...Array(5)].map((_, i) => (
                  <svg
                    key={i}
                    className="h-5 w-5 fill-current"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>
              
              <blockquote className="mt-4 text-[color:var(--text)]">
                &quot;{testimonial.quote}&quot;
              </blockquote>
              
              <div className="mt-6 flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[color:var(--accent)]/10 text-sm font-semibold text-[color:var(--accent)]">
                  {testimonial.avatar}
                </div>
                <div>
                  <div className="font-semibold text-[color:var(--text-strong)]">
                    {testimonial.author}
                  </div>
                  <div className="text-sm text-[color:var(--text-muted)]">
                    {testimonial.role}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
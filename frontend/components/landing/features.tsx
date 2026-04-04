"use client";

const features = [
  {
    title: "Matching intelligent",
    description: "Notre algorithme proprietaire analyse les competences, l'experience et les preferences pour trouver le candidat ideal.",
    icon: "🎯",
    gradient: "from-blue-500 to-cyan-400",
  },
  {
    title: "Analytics avancees",
    description: "Visualisez vos donnees avec des graphiques interactifs. Suivez les tendances et optimisez vos placements.",
    icon: "📊",
    gradient: "from-purple-500 to-pink-400",
  },
  {
    title: "Collaboration multi-utilisateurs",
    description: "Travaillez en equipe avec des roles et permissions granulaires. Partagez profils et missions facilement.",
    icon: "👥",
    gradient: "from-orange-500 to-yellow-400",
  },
  {
    title: "Import en masse",
    description: "Importez vos profils existants depuis CSV, JSON ou connectez vos outils RH via notre API.",
    icon: "📥",
    gradient: "from-green-500 to-emerald-400",
  },
  {
    title: "Shortlists intelligentes",
    description: "Creez des shortlists personnalisees et partagez-les avec vos clients en un clic.",
    icon: "📋",
    gradient: "from-red-500 to-rose-400",
  },
  {
    title: "Securite enterprise",
    description: "Vos donnees sont chiffrees en repos et en transit. Conformite RGPD garantie.",
    icon: "🔒",
    gradient: "from-indigo-500 to-violet-400",
  },
];

export function Features() {
  return (
    <section id="features" className="py-20 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-[color:var(--text-strong)] sm:text-4xl">
            Tout ce dont vous avez besoin
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-[color:var(--text)]">
            Une plateforme complete pour gerer vos profils, missions et matchings en toute simplicite.
          </p>
        </div>
        
        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="group relative rounded-2xl border border-black/10 bg-white p-8 shadow-sm transition hover:shadow-lg"
            >
              <div
                className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${feature.gradient} text-2xl`}
              >
                {feature.icon}
              </div>
              <h3 className="text-xl font-semibold text-[color:var(--text-strong)]">
                {feature.title}
              </h3>
              <p className="mt-3 text-[color:var(--text)]">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
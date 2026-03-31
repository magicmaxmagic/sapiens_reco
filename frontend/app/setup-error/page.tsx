export default function SetupErrorPage() {
  return (
    <main className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-7xl items-center px-4 py-10 sm:px-6 lg:px-8">
      <section className="mx-auto w-full max-w-2xl rounded-2xl border border-amber-300 bg-amber-50 p-6 shadow-[0_20px_60px_-45px_rgba(146,64,14,0.55)]">
        <p className="text-xs uppercase tracking-[0.16em] text-amber-700">Configuration requise</p>
        <h1 className="mt-2 text-2xl font-semibold text-amber-900">Connexion indisponible</h1>
        <p className="mt-3 text-sm text-amber-900">
          L&apos;application est protegee par login global, mais la variable APP_LOGIN_SESSION_SECRET
          n&apos;est pas configuree.
        </p>

        <div className="mt-5 rounded-xl border border-amber-300 bg-white p-4 text-sm text-amber-900">
          <p className="font-medium">Action necessaire</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>Local: definir APP_LOGIN_SESSION_SECRET dans frontend/.env.local</li>
            <li>Vercel: definir APP_LOGIN_SESSION_SECRET dans les variables du projet</li>
            <li>Redemarrer le serveur frontend apres mise a jour des variables</li>
          </ul>
        </div>
      </section>
    </main>
  );
}
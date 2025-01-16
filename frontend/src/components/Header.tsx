export const Header = () => {
  return (
    <header className="flex items-center gap-4 p-4">
      <a
        href="/"
        className="text-xl font-bold transition-colors hover:text-foreground/80 text-foreground"
      >
        MS Encoding Competition
      </a>
      <nav className="space-x-4">
        <a
          href="/submit"
          className="transition-colors hover:text-foreground/80 text-foreground"
        >
          Submit
        </a>
        <a
          href="/ranking"
          className="transition-colors hover:text-foreground/80 text-foreground"
        >
          Ranking
        </a>
      </nav>
    </header>
  );
};

import Link from "next/link";

export function NavBar() {
  return (
    <nav className="flex gap-6 text-sm font-medium text-zinc-600 dark:text-zinc-400">
      <Link href="/" className="hover:text-black dark:hover:text-zinc-50">
        Guest Chat
      </Link>
      <Link href="/host" className="hover:text-black dark:hover:text-zinc-50">
        Host Dashboard
      </Link>
    </nav>
  );
}

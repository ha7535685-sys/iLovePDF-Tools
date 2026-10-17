import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        name: { label: "Name", type: "text" },
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (credentials?.email && credentials?.password) {
          const rawName = credentials.name?.trim();
          let displayName = rawName;
          if (!displayName) {
            const prefix = credentials.email.split("@")[0] || "User";
            displayName = prefix.charAt(0).toUpperCase() + prefix.slice(1);
          }
          return {
            id: credentials.email,
            name: displayName,
            email: credentials.email,
          };
        }
        return null;
      }
    })
  ],
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.name = user.name;
        token.email = user.email;
      }
      return token;
    },
    async session({ session, token }) {
      if (token && session.user) {
        session.user.name = token.name as string;
        session.user.email = token.email as string;
      }
      return session;
    }
  },
  secret: process.env.NEXTAUTH_SECRET || "super-secret-default-key-for-local-dev-ilovepdf",
});

export { handler as GET, handler as POST };

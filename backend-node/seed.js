require("dotenv").config();
const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

async function main() {
  const existing = await prisma.user.findUnique({ where: { id: "test-user" } });
  if (existing) {
    console.log("User 'test-user' sudah ada, tidak perlu dibuat ulang.");
    return;
  }

  const user = await prisma.user.create({
    data: {
      id: "test-user",
      email: "test@akademikai.local",
      password: "dummy-not-used",
      name: "Test User (Dummy)",
      role: "student",
    },
  });

  console.log("User dummy berhasil dibuat:", user);
}

main()
  .catch((e) => console.error(e))
  .finally(() => prisma.$disconnect());

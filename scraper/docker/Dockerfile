# Use the official Bun image
FROM oven/bun:latest

# Set the Docker working directory as /usr/src/app
WORKDIR /usr/src/app

# Copy everything from the current directory into Docker's /usr/src/app
COPY . .

RUN bun install

# Run the project
CMD bun run index.ts
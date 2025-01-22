FROM node:22-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN yarn install

# Copy the rest of the application code
COPY . .

# Build the Next.js project
RUN yarn build

# Expose the application port
EXPOSE 3000

# Command to run the Next.js app
CMD ["yarn", "start"]
FROM public.ecr.aws/docker/library/node:24.2.0-bullseye
# Use the official AWS Lambda Web Adapter image for x86_64 architecture
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1-x86_64 /lambda-adapter /opt/extensions/lambda-adapter
# Ensure the lambda adapter has proper execution permissions
RUN chmod +x /opt/extensions/lambda-adapter
EXPOSE 8080
WORKDIR "/var/task"
ADD src/package.json /var/task/package.json
ADD src/package-lock.json /var/task/package-lock.json
RUN npm install --omit=dev
ADD src/ /var/task
CMD ["node", "index.js"]
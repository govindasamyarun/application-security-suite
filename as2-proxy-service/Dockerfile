FROM nginx:1.19.6

# # Copy default and nginx conf files  
COPY default.conf /etc/nginx/conf.d/
COPY nginx.conf /etc/nginx/

# Copy the source code to application home directory 
COPY . /usr/share/nginx

# Create application user 
RUN groupadd -r -g 110 www && \
    useradd as2 -u 1001 -g 110 -m -s /bin/bash && \
    chown -R as2:www /usr/share/nginx && \
    chmod -R 764 /usr/share/nginx && \
    chmod -R 755 /etc/nginx/

# Run the container as non-root user 
USER as2

# Set the working directory 
WORKDIR /usr/share/nginx

# Expose ports 
EXPOSE 8011 80

# Start the application  
CMD ["nginx", "-g", "daemon off;"]
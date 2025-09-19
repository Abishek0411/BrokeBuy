#!/bin/bash

# MongoDB Atlas Export Script
# This script exports data from MongoDB Atlas to local files

echo "Starting MongoDB Atlas data export..."

# Create backup directory
mkdir -p ./atlas_backup

# Export from Atlas (you'll need to replace the connection string with your actual Atlas URI)
echo "Exporting data from MongoDB Atlas..."
mongodump --uri="mongodb+srv://abishekram0411:Dt1Fcyqxbkz0yFu7@cluster0.gab1psq.mongodb.net/brokebuy?retryWrites=true&w=majority&appName=Cluster0" --out=./atlas_backup

echo "Export completed! Data saved to ./atlas_backup directory"
echo "Collections exported:"
ls -la ./atlas_backup/brokebuy/

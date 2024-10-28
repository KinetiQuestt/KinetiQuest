from flask import Flask
from flask_restx import Api, Resource, fields, reqparse, Namespace
from app.app import app, api
from app.models import db, User, Quest, QuestCopy, Pet

ns = Namespace('resources', description="requests related to users and associated methods")
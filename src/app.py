from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)
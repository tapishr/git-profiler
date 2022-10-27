from operator import attrgetter
import sys
from git import Repo
from language import LanguageExtractor
import plotly.graph_objects as gobj
import numpy as np
import datetime


class RepositoryProfiler:
	def __init__(self, repo_path, num_days=90):
		self.repo = Repo(repo_path)
		self.user_emails = set()
		self.user_emails.add(self.getUserEmail())
		self.num_days = num_days

	def getUserEmail(self):
		reader = self.repo.config_reader()
		val = reader.get_value("user", "email")
		return val

	def addUserEmails(self, emails):
		for email in emails:
			self.user_emails.add(email)

	def getCommitsList(self, number_of_commits):
		commits_list = list(self.repo.iter_commits('master', max_count=number_of_commits))
		self.latest = commits_list[0].committed_datetime
		print("Total number of commits:", len(commits_list))
		commits_list = [c for c in commits_list if c.author.email in self.user_emails and (self.latest - c.committed_datetime).days < self.num_days]
		print("Number of your commits:", len(commits_list))
		return commits_list

	def retrieveDiffs(self, commits_list):
		contributions = {}
		le = LanguageExtractor()
		for commit in commits_list:
			file_changes = commit.stats.files
			for filename in file_changes.keys():
				try:
					fname = filename[filename.rindex("/")+1:]
				except ValueError:
					fname = filename
				language = le.get_language_from_file(fname)
				if language == None:
					language = 'Others'
				if language not in contributions:
					contributions[language] = {}
				cdate = str(commit.committed_date)
				if cdate not in contributions[language]:
					contributions[language][cdate] = 0
				contributions[language][cdate] += file_changes[filename]['lines']
		return contributions

	def getProfile(self):
		commits_list = self.getCommitsList(number_of_commits=None)
		contributions = self.retrieveDiffs(commits_list)
		langs = list(contributions.keys())
		dates = self.latest - np.arange(self.num_days) * datetime.timedelta(days=1)
		fig = gobj.Figure(data=gobj.Heatmap(
			z=self.getDepth(contributions, langs),
			x=dates,
			y=langs,
			colorscale='blackbody'))
		fig.show()

	def getDepth(self, contributions, langs):
		depth = []
		for lang in langs:
			langdepth = np.zeros(self.num_days)
			for cdate in contributions[lang]:
				langdepth[datetime.timedelta(seconds=self.latest.timestamp() - float(cdate)).days] = contributions[lang][cdate]
			langdepth = langdepth/np.sum(langdepth)
			depth.append(langdepth)
		return depth
#!/usr/bin/python3

import os

timeformat='%Y-%m-%d %H:%M'

class Test:
	def __init__(self, test, path=None):
		"""
		Runs that test, and stores the results.
		
		@param test is the path to get to the executable, 
		@param path is where to execute it. By default same as test.
		"""
		self.success=True
		self.test=os.path.abspath(test)
		if path:
			self.path=os.path.abspath(path)
		else:
			self.path=os.path.dirname(self.test)
		print('Testing %s at %s'%(self.test,self.path))
		self.tests={}
		self.run()
		
	def run(self):
		"""
		Runs the prepared test.
		"""
		try:
			import subprocess, datetime
			self.starttime=datetime.datetime.now()
			self.subprocess=subprocess.Popen(self.test, stderr=subprocess.PIPE, close_fds=True, cwd=self.path, env={ 'CTEST_LOG':'1' })
			current_f=None
			for line in self.subprocess.stderr.readlines():
				line=line.decode('utf8')
				if line.startswith("CTEST"):
					line=line.split()
					cmd=line[2]
					if cmd=='start':
						current_f=line[3]
						self.tests[current_f]=dict(ok=0,fail=0,detail=[])
					else:
						self.tests[current_f]['detail'].append((line[2],line[1]))
						if line[2]=='ok':
							self.tests[current_f]['ok']+=1
						elif line[2]=='fail':
							self.tests[current_f]['fail']+=1
							
				else:
					print(line,end='')
			self.error_msg=''
			self.endcode=self.subprocess.wait()
			self.success=(self.endcode==0)
		except Exception as e:
			import traceback
			traceback.print_exc()
			print('*********')
			self.error_msg=str(e)
			self.endcode=False
			self.success=False
		
	def stats(self):
		print('*************************************************************************')
		print('Final stats:')
		total_ok=sum([x['ok'] for x in self.tests.values()])
		total_fail=sum([x['fail'] for x in self.tests.values()])
		total=total_ok+total_fail
		if total==0:
			print ("No test were run")
		else:
			print('%d/%d; %.2f %% Success rate.'%(total_ok, total, (total_ok*100.0)/total))
		if self.endcode!=0:
			print("Process DID not finished properly. Exit status %d"%self.endcode)

	def html_fd(self, fd):
		fd.write('<div class="cmd">')
		fd.write('<h2>%s</h2>'%self.test)
		fd.write('<div class="info">%s<br/>'%self.starttime.strftime(timeformat))
		
		total_ok=sum([x['ok'] for x in self.tests.values()])
		total_fail=sum([x['fail'] for x in self.tests.values()])
		total=total_ok+total_fail
		
		if total==0:
			fd.write('<b class="fail">No test were run</b>')
		else:
			klass="mid"
			if total_ok==total:
				klass='ok'
			if total_ok==0:
				klass='fail'
				
			fd.write('%d/%d; <span class="%s">%.2f %% Success rate.</span>'%(total_ok, total, klass, (total_ok*100.0)/total))
		if self.endcode!=0:
			fd.write('<br><b class="fail">Process DID not finished properly. Exit status %d</b>'%self.endcode)
		if self.error_msg:
			fd.write('<br><b class="fail">%s</b>'%self.error_msg)
		fd.write('</div>')
		for t in self.tests.items():
			self.html_test(fd, *t)
		fd.write('<hr/></div>')
			
	def html_test(self, fd, name, data):
		fd.write('<div class="test"><b>%s</b><span class="test_count">%d tests</span>'%(name,len(data['detail'])))
		fd.write('<table class="test"><tr>')
		for i in data['detail']:
			fd.write('<td class="%s" title="%s"></td>'%(i[0],i[1]))
		fd.write('</tr></table></div>')

class TestSuite:
	def __init__(self):
		self.html('index.html')
		self.success=True

	def close(self):
		self.fd.write('</html>')
		del self.fd

		
	def html(self, filename):
		import datetime
		fd=open(filename,'w')
		self.fd=fd
		fd.write('<html><head><style>'+
"""
.test{
	clear: both;
}
.test table{
	width: 100%;
	border-collapse: collapse;
}
.test tr{
	height: 1em;
}
.test td.ok:nth-child(2n) {
	background: green;
}
.test td.ok:nth-child(2n+1) {
	background: forestgreen;
}
.test td.ok:nth-child(2n+1):hover{
	background: limegreen;
}
.test td.ok:nth-child(2n):hover{
	background: limegreen;
}
.test .test_count{
	float: right;
}
.ok{
	background: forestgreen;
	color: white;
	border-radius: 2px;
}
.fail{
	background: red;
	border-radius: 2px;
}
.fail[title]:hover{
	background: orangered;
}
h1 img{
	float: right;
}
.info{
	float: right;
	border: 1px solid #eee;
	border-radius: 5px;
	margin-top: 0px;
	margin-bottom: -2em;
	box-shadow: 0px 2px 2px rgba(0,0,0,0.5);
	position: relative;
	top: -3em;
}
.cmd{
	clear: both;
}
hr{
	clear: both;
	width: 50%;
	height: 1px;
	border-collapse: collapse;
}
"""+'<style src="style.css"></style></head><html>'+
		'<h1>CTest results: %s<a href="http://www.coralbits.com"><img src="http://www.coralbits.com/staticc/images/logo500.png"/></a></h1>'%(datetime.datetime.now().strftime(timeformat)))
		fd.write('<div style="clear: both;"></div>')
		
	def test(self,cmd):
		test=Test(cmd)
		test.html_fd(self.fd)
		self.success=self.success  or test.success
		
def main():
	import sys
	suite=TestSuite()
	for i in sys.argv[1:]:
		suite.test(i)
	suite.close()
	return suite.success

if __name__=='__main__':
	import sys
	if main():
		sys.exit(0)
	sys.exit(1) # error on some test

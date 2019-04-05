from string import Template

from django.core.management.base import BaseCommand, CommandError
import django
from django.conf import settings
#from polls.models import Question as Poll
from pprint import pprint
from clint.textui import progress
import requests
import os
import zipfile
#import uuid
import shutil
from pprint import pprint

django.setup()

class Command(BaseCommand):
    help = 'Generates CRUD operations based on a model using the sbadmin2 template'

    def add_arguments(self, parser):
        print(settings.BASE_DIR)
        #parser.add_argument('modelname', nargs='+', type=string)
        parser.add_argument('appname')
        parser.add_argument('modelname')


    def handle(self, *args, **options):
        appname = options['appname']
        modelname = options['modelname']
        appdir = settings.BASE_DIR + os.sep + str(appname)

        if not self.app_exists(appname):
            print('Não existe uma app chamada: ' + appname)
            exit()

        print('creates a ' + appname + os.sep + "urls.py file if it doesn't exist")
        self.touch(appdir + os.sep + 'urls.py')

        try:
            exec('from ' + appname + '.models import ' + modelname)
        except ImportError as e:
            print(str(e))
            print("Probaly the model '" + modelname+ "' doesn't exists")
            exit(4)


        self.get_bootstrap_data(appname)

        print('creating template folder')
        self.create_template_folder(appname)
        print('changing settings of project')
        self.change_settings_file()
        print('changing urls.py of project')
        self.change_urls_py_project(appname)
        print('changing urls.py of app')
        self.change_urls_py_app(appname, [modelname])
        print('changing base_template')
        self.change_base_template(appname, [modelname])
        print('creating templates')
        self.create_templates(appname, [modelname])
        print('creating views')
        self.create_views(appname, [modelname])
        print('creating tables')
        self.create_tables(appname, [modelname])
        print('finishing...')



    def touch(self, filename):
        if not self.fileExists(filename):
            fo = open(filename, 'w')
            fo.write('')
            fo.close()

    def unzip(self, filename, destination):
        fantasy_zip = zipfile.ZipFile(filename)
        fantasy_zip.extractall(destination)
        fantasy_zip.close()

    def downloadfile_with_progress_bar(self, url, destination):
        http_proxy = ''
        https_proxy = ''
        ftp_proxy = ''
        if 'http_proxy' in os.environ:
            http_proxy = os.environ['http_proxy']
        if 'https_proxy' in os.environ:
            https_proxy = os.environ['https_proxy']
        if 'ftp_proxy' in os.environ:
            ftp_proxy = os.environ['ftp_proxy']
        self.downloadfile_with_progress_bar_with_proxies(url, destination, http_proxy=http_proxy, https_proxy=https_proxy,
                                                    ftp_proxy=ftp_proxy)

    def downloadfile_with_progress_bar_with_proxies(self, url, destination, http_proxy='', https_proxy='', ftp_proxy='',
                                                    verify=False):
        proxyDict = {}
        if http_proxy != '':
            proxyDict['http'] = http_proxy
        if https_proxy != '':
            proxyDict['https'] = https_proxy
        if ftp_proxy != '':
            proxyDict['ftp'] = ftp_proxy
        r = requests.get(url, proxies=proxyDict, stream=True, verify=verify)
        if 'Content-Length' not in r.headers:
            print('Não foi possível efectuar download do ficheiro')
            pprint(r.headers)
            exit()
        with open(destination, 'wb') as f:
            total_length = int(r.headers.get('Content-Length'))
            for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1):
                if chunk:
                    f.write(chunk)
                    f.flush()

    def app_exists(self, appname):
        appdir = settings.BASE_DIR + os.sep + str(appname)
        if os.path.isdir(appdir):
            return True
        return False

    def get_bootstrap_data(self, appname):
        appdir = settings.BASE_DIR + os.sep + str(appname)
        static_appdir = appdir + os.sep + 'static'

        base_template_folder = self.getDjangoProjectPath() + os.sep + appname + os.sep + 'templates' + os.sep + 'base.html'
        if self.fileExists(base_template_folder):
            fi = open(base_template_folder)
            txt = fi.read()
            fi.close()
            if '<!-- LOOP MODEL MENU -->' in txt:
                self.stdout.write(self.style.WARNING("\n\n"))
                self.stdout.write(self.style.WARNING("*****************************************************"))
                self.stdout.write(self.style.WARNING('It seems "scaffold-model" was executed at least once!'))
                self.stdout.write(self.style.WARNING("*****************************************************"))
                self.stdout.write(self.style.WARNING(''))
                return True

        print(static_appdir)
        if os.path.isdir(static_appdir):
            self.stdout.write(self.style.WARNING('Warning: App "' + appname + '" already have a static folder!'))
            self.stdout.write(self.style.WARNING('If you reply "yes", you will overwrite the "static" folder!'))
            self.stdout.write(self.style.WARNING(''))

            self.stdout.write(self.style.WARNING())
            yesno_vals = ['YES', 'NO', 'Y', 'N']
            yesno = ''
            while yesno not in yesno_vals:
                yesno = input('Can I overwrite the files in "static" folder(yes/no)? ').upper()
            if yesno in ['YES', 'Y']:
                shutil.rmtree(static_appdir)
                self.download_and_unzip(appname)
            else:
                """
                self.stdout.write(self.style.WARNING("ok... you don't trust me to delete it..."))
                self.stdout.write(self.style.WARNING('I will download and unzip the necessary files to "' + appdir + os.sep + 'startbootstrap-sb-admin-2-master", so...'))
                self.stdout.write(self.style.WARNING("you must merge the files by hand! Have fun!"))
                self.download_and_unzip(appname, rename=False)
                """
                self.stdout.write(self.style.WARNING("ok... you don't trust me to delete it..."))
                self.stdout.write(self.style.WARNING('I will download the data file to here: "' + appdir + os.sep + 'lixo.zip", so...'))
                self.stdout.write(self.style.WARNING("you must merge the files by hand! Have fun!"))
                self.downloadFile()
        else:
            self.download_and_unzip(appname)


    def downloadFile(self):
        zipname = 'https://github.com/brunogoncalooliveira/django-scaffold-bootstrap/blob/master/sbadmin_data.zip?raw=true'
        self.downloadfile_with_progress_bar(zipname, 'lixo.zip')

    def download_and_unzip(self, appname, rename=True):
        appdir = settings.BASE_DIR + os.sep + str(appname)

        self.downloadFile()

        print('unzipping file...')
        self.unzip('lixo.zip', appdir)
        #if rename:
        #    os.rename(appdir + os.sep + 'sbadmin_data', static_appdir)

    def project_name(self,):
        return os.path.basename(settings.BASE_DIR)

    def change_settings_file(self):

        filepath = self.getDjangoProjectPath() + os.sep + self.project_name() + os.sep + 'settings.py'
        fi = open(filepath)
        t = fi.read()
        fi.close()

        s = ''
        if settings.STATIC_URL is None:
            s += "STATIC_URL = '/static/'\n"

        if settings.STATIC_ROOT is None:
            s += "STATIC_ROOT = os.path.join(BASE_DIR, 'static')\n"
            self.saveOrAppendToFile(s, filepath)

        try:
            a = settings.MESSAGE_TAGS
        except AttributeError:
            s += """
# THIS WAS ADDED BY A SCRIPT
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}
"""
        if 'logging.basicConfig' not in t:
            s += """
import logging

logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(levelname)s %(module)s %(funcName)s: %(message)s',
)
"""

        if 'django_tables2' not in settings.INSTALLED_APPS:
            s += "INSTALLED_APPS.append('django_tables2')\n"
        if 'widget_tweaks' not in settings.INSTALLED_APPS:
            s += "INSTALLED_APPS.append('widget_tweaks')\n"
        if s != '':
            self.saveOrAppendToFile(s, filepath)



    def getDjangoProjectPath(self):
        #return os.path.dirname(os.path.realpath(__file__))
        return settings.BASE_DIR

    def createFolder(self, directory):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
        except OSError:
            print ('Error: Creating directory. ' +  directory)


    def getNextFilename(self, filepath):
        try:
            cnt = int(filepath.split('.')[-1])
        except ValueError:
            cnt = 1

        tmp_filepath = filepath
        while self.fileExists(tmp_filepath):
            tmp_filepath = filepath + '.scaffold-bootstrap.' + str(cnt)
            cnt +=1

        return tmp_filepath

    def fileExists(self, filepath):
        if os.path.isfile(filepath) and os.access(filepath, os.R_OK):
            return True
        else:
            return False

    def backupFile(self, filename):
        t_filename = self.getNextFilename(filename)
        if self.fileExists(filename):
            shutil.copyfile(filename, t_filename)

    def saveToFileNoOverride(self, mystr, filename):
        #
        # not used!!!
        #
        if self.fileExists(filename):
            fi = open(filename)
            s = fi.read()
            fi.close()
            if s == mystr: # se o conteúdo do ficheiro é o mesmo, não se faz nada...
                return ''  # não há necessidade de sobrepor o ficheiro
            filename = self.getNextFilename(filename)
        return self.saveToFile(mystr, filename)

    def saveToFile(self, mystr, filename):
        self.backupFile(filename)
        fo = open(filename, 'w', encoding='utf-8')
        fo.write(mystr)
        fo.close()

    def saveOrAppendToFile(self, s, filepath):
        if self.fileExists(filepath):
            self.backupFile(filepath)
            fi = open(filepath)
            t = fi.read()
            fi.close()
            if s not in t:
                with open(filepath, "a") as myfile:
                    myfile.write(s)
        else:
            self.saveToFile(s, filepath)

    def unzip_sbadmin_data(self, app_name):
        filename = 'sbadmin_data.zip'
        fantasy_zip = zipfile.ZipFile(filename)
        fantasy_zip.extractall(self.getDjangoProjectPath() + os.sep + app_name)
        fantasy_zip.close()

    def create_template_folder(self, app_name):
        templates_folder = self.getDjangoProjectPath() + os.sep + app_name + os.sep + 'templates' + os.sep + app_name
        print(templates_folder)
        #app_folder = getScriptDirPath() + os.sep + app_name
        self.createFolder(templates_folder)


    def change_urls_py_project(self, app_name):

        ###
        ###    urls.py
        ###
        filepath = self.getDjangoProjectPath() + os.sep + self.project_name() + os.sep + 'urls.py'
        fi = open(filepath)
        t = fi.read()
        fi.close()

        if app_name not in t:
            s = """\n\n# THIS WAS ADDED BY A SCRIPT
from django.conf.urls import include, url
    
urlpatterns.append( url(r'', include(('""" + app_name + ".urls', '" + app_name + "'), namespace='" + app_name + """')))\n"""

            self.saveOrAppendToFile(s, filepath)



    def change_urls_py_app(self, app_name, model_name):
        app_folder = self.getDjangoProjectPath() + os.sep + app_name
        filepath = app_folder + os.sep + 'urls.py'

        s = """\n#------------------------------
# THIS WAS ADDED BY A SCRIPT
#------------------------------
from django.conf.urls import url
from . import views

urlpatterns = []
"""

        fi = open(filepath)
        txt = fi.read()
        fi.close()
        if '# THIS WAS ADDED BY A SCRIPT' in txt or 'urlpatterns = []' in txt:
            s=''

        for model in model_name:
            s += "urlpatterns.append( url(r'^" + model + "_list/$', views." + model + "List, name='" + model + "_list'))\n"
            s += "urlpatterns.append( url(r'^" + model + "_new/$', views." + model + "New, name='" + model + "_new'))\n"
            s += "urlpatterns.append( url(r'^" + model + "_edit/(?P<id>[0-9]+)/$', views." + model + "Edit, name='" + model + "_edit'))\n"

        self.saveOrAppendToFile(s, filepath)


    def change_base_template(self, app_name, model_name):
        base_template_folder = self.getDjangoProjectPath() + os.sep + app_name + os.sep + 'templates' + os.sep + 'base.html'
        fi = open(base_template_folder )
        t = fi.read()
        fi.close()

        s = ''
        for model in model_name:
            list_template = """
                        <li>
                            <a href="{% url '${app_name}:${model}_list' %}"><i class="fa fa-book fa-fw"></i> ${model}</a>
                        </li>
<!-- LOOP MODEL MENU -->
"""
            src = Template( list_template )
            d={ 'app_name': app_name, 'model': model}
            file_content = src.substitute(d)
            s += file_content

        s = t.replace("<!-- LOOP MODEL MENU -->", s)
        fo = open(base_template_folder, "w" )
        fo.write(s)
        fo.close()



    def generate_list_template(self, app_name, model_name):
        list_template = """{% extends 'base.html' %}
    {% load render_table from django_tables2 %}
    {% load model_name %}
    {% block content %}
    <div class="row">
        <div class="col-lg-12">
            <h1 class="page-header">{% model_name_plural model %}</h1>
        </div>
        <!-- /.col-lg-12 -->
    </div>
    <div class="row">
        <div class="col-lg-12">
            <!-- /.panel -->
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-bar-chart-o fa-fw"></i> List
                </div>

                <div class="panel-body">
                    {% render_table table %}
                </div>

            </div>
            <!-- /.panel -->
        </div>
        <!-- /.col-lg-4 -->
    </div>
    <div class="row">
        <div class="col-lg-12">
          <a href="{% url '${app_name}:${model_name}_new' %}" class="btn btn-primary">New {% model_name model %}</a>
        </div>
    </div>

    <!-- /.row -->
    {% endblock %}"""
        src = Template( list_template )
        d={ 'app_name': app_name, 'model_name': model_name}
        file_content = src.substitute(d)
        return file_content


    def generateValidations(self, app_name, model_name, selector):
        model_name = model_name[0]

        txt = ''
        exec('from ' + app_name + '.models import ' + model_name)
        fields = []
        for i in eval(model_name + '._meta.fields'):
            if i.name != 'id' and i.blank == False:
                txt += i.name + "_regex = /^.+$/;\n"
                txt += 'valid_' + i.name + " = regex_validate_field('" + i.name + "', " + i.name + "_regex, 'This field cannot be empty');\n"
                fields.append(i.name)

        if len(fields) == 0:
            txt = ''
        else:
            tfields = []
            for i in fields:
                tfields.append('valid_' + i)
            fields = tfields
            txt += 'if ( ' + (' && ').join(fields) + ") {\n"
            txt += """        $('""" + selector + """').removeClass('disabled');
                return true;
            } else {
                $('""" + selector + """').addClass('disabled');
                return false;
            };
        """
        return txt

    def regex_validate_field(self):
        txt = """    function regex_validate_field(id, regex, message) {
        $("#erro_" + id).remove();
        var inputVal = $('#id_' + id).val();

        if(!regex.test(inputVal)) {
            $('#id_' + id).after('<small id="erro_' + id + '" class="error error-keyup-3 form-text text-muted ">' + message + '</small>');
            return false;
        } else {
            $('#erro_' + id).remove();
            return true;
        }
    }
"""
        return txt

    def generate_Edit_template(self, app_name, model_name):
        txt = self.generateValidations(app_name, model_name, '#butSubmit[value=save]')

        edit_template = """{% extends 'base.html' %}
    {% load render_table from django_tables2 %}
    {% load model_name %}
    {% load static %}
    {% block content %}
    <div class="row">
        <div class="col-lg-12">
            <h1 class="page-header">Edit {% model_name model %}</h1>
        </div>
        <!-- /.col-lg-12 -->
    </div>



    <div class="row">
        <div class="col-lg-12">
            <!-- /.panel -->
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-bar-chart-o fa-fw"></i> Fill in the form
                </div>

                <div class="panel-body">

                <form method="post" name="form1" id="form1" enctype="multipart/form-data">
                  {% csrf_token %}
                  {% include 'includes/bs4_form.html' with form=form %}

                      <div class="form-group">
                          <button href="#" id="butSubmit" name="accao" value="save" class="btn btn-primary" onclick="javascript:$('#form1').submit();var loading = new Loading();">Edit</button>
                          <span class="pull-right button-group">
                              <button id="but_showmodal" class="btn btn-danger" onclick="javascript:ShowModal();return false;">Delete</button>
                          </span>
                            <div id="modal1"></div>
                      </div>
                </form>
            </div>
            <!-- /.panel -->
        </div>
        <!-- /.col-lg-4 -->
    </div>

    {% endblock %}
    {% block jqueryscript %}
    <script>

    function ShowModal() {
        doModal('modal1', 'Delete Request', 'This action will delete this record<p></p>Do you want to continue?', 'Yes!', 'No, take me out of here!');
    }

    %%%%%%regex_validate_field%%%%%%


    function validate_fields() {
        %%%%%%validations%%%%%%

        return true;
    }


$(document).ready(function() {

    $("#form1").keypress(function(e) {
        // Ao carregar-se em Enter, a form não é submetida se retornar fal-se
        if (e.which == 13) {
            if (validate_fields()) {
                ShowModal();
            }
            return false;
          }
    });
        
    $('.form-control').on('input change keyup paste', function() {
        console.log('b');
        $('.invalid-feedback').remove();
        validate_fields();
    });

    validate_fields();
});
</script>
{% endblock %}
"""
        return edit_template.replace('%%%%%%validations%%%%%%', txt).replace( '%%%%%%regex_validate_field%%%%%%' , self.regex_validate_field())

    def generate_New_template(self, app_name, model_name):
        txt = self.generateValidations(app_name, model_name, '#butSubmit')

        new_template = """{% extends 'base.html' %}
{% load render_table from django_tables2 %}
{% load model_name %}
{% load static %}
{% block content %}
<div class="row">
    <div class="col-lg-12">
        <h1 class="page-header">Create {% model_name model %}</h1>
    </div>
    <!-- /.col-lg-12 -->
</div>



<div class="row">
    <div class="col-lg-12">
        <!-- /.panel -->
        <div class="panel panel-default">
            <div class="panel-heading">
                <i class="fa fa-bar-chart-o fa-fw"></i> Fill in the form
            </div>

            <div class="panel-body">

                <form method="post" name="form1" id="form1" enctype="multipart/form-data">
                  {% csrf_token %}
                  {% include 'includes/bs4_form.html' with form=form %}

                      <div class="form-group">
                            <a href="#" id="butSubmit" class="btn btn-danger" onclick="javascript:$('#form1').submit();var loading = new Loading();">Create</a>
                            <div id="modal1"></div>
                      </div>

                </form>
            </div>

        </div>
        <!-- /.panel -->
    </div>
    <!-- /.col-lg-4 -->
</div>

{% endblock %}
{% block jqueryscript %}
<script>

function ShowModal() {
    doModal('modal1', 'Delete Request', 'This action will create a new record<p></p>Do you want to continue?', 'Yes!', 'No, take me out of here!');
}

%%%%%%regex_validate_field%%%%%%

function validate_fields() {
    %%%%%%validations%%%%%%

    return true;
}


$(document).ready(function() {

$("#form1").keypress(function(e) {
    // Ao carregar-se em Enter, a form não é submetida se retornar false
    if (e.which == 13) {
        if (validate_fields()) {
            ShowModal();
        }
        return false;
      }
    });
    $('.form-control').on('input change keyup paste', function() {
        $('.invalid-feedback').remove();
        validate_fields();
    });

    validate_fields();
});
</script>
{% endblock %}
"""
        return new_template.replace('%%%%%%validations%%%%%%', txt).replace( '%%%%%%regex_validate_field%%%%%%' , self.regex_validate_field())


    def generateViewList(self, app_name, model_name):
        list_template = """def ${model_name}List(request):
    table = ${model_name}Table(${model_name}.objects.all())
    RequestConfig(request).configure(table)
    table.paginate(page=request.GET.get('page', 1), per_page=5)
    return render(request, '${app_name}/${model_name}_list.html', {'table': table, 'model': ${model_name}, 'menu_name': '${model_name}'})

"""
        src = Template( list_template )
        d={ 'app_name': app_name, 'model_name': model_name}
        file_content = src.substitute(d)
        return file_content


    def generateFormModel(self, app_name, model_name):
        fields = ''

        exec('from ' + app_name + '.models import ' + model_name)

        for i in eval(model_name + '._meta.fields'):
            if i.name != 'id':
                fields += "'" + i.name + "', "
        fields = fields.strip(', ')

        FormModelTemplate = """
class ${model_name}Form(forms.ModelForm):
    class Meta:
        model = ${model_name}
        fields = (${fields})
"""

        src = Template( FormModelTemplate )
        d={ 'model_name': model_name, 'fields': fields}
        file_content = src.substitute(d)

        return file_content



    def generateViewEdit(self, app_name, model_name):
        edit_template = """
def ${model_name}Edit(request, id):
    req = get_object_or_404(${model_name}, id=id)

    if request.method != 'POST':
        form = ${model_name}Form(instance=req)
    else:
        form = ${model_name}Form(request.POST, instance=req)
        accao = request.POST.get('accao', '')
        if accao == 'save':
            if request.POST and form.is_valid():
                form.save()
                messages.success(request, 'Request saved!')
            else:
                messages.error(request, 'An error occurred saving data!')
            return HttpResponseRedirect(reverse('${app_name}:${model_name}_list'))
        else:
            if accao == 'delete':
                ${model_name}.objects.get(pk=id).delete()
                messages.success(request, 'Record deleted!')
                return HttpResponseRedirect(reverse('${app_name}:${model_name}_list'))
            else:
                messages.success(request, 'A error happened while processing the form.')
                return HttpResponseRedirect(reverse('${app_name}:${model_name}_list'))

    return render(request, 'polls/Question_edit.html', {'form': form, 'model': ${model_name}, 'menu_name': '${model_name}'})
"""
        src = Template( edit_template )
        d={ 'app_name': app_name, 'model_name': model_name}
        file_content = src.substitute(d)
        return file_content

    def generateViewNew(self, app_name, model_name):
        list_template = """
def ${model_name}New(request):
    if request.method == 'GET':
        form = ${model_name}Form()
    else:
        form = ${model_name}Form(request.POST)
        if form.is_valid():
            form.save()
            request.session['success'] = 'Record Saved'
            return HttpResponseRedirect(reverse('${app_name}:${model_name}_list'))
        else:
            messages.error(request, mark_safe("The following fields have invalid data:<br>" + str(form.errors)))

    return render(request, '${app_name}/${model_name}_new.html', {'form': form, 'model': ${model_name}, 'menu_name': '${model_name}'})

    """
        src = Template( list_template )
        d={ 'app_name': app_name, 'model_name': model_name}
        file_content = src.substitute(d)
        return file_content


    def generateTable(self, app_name, model_name):

        exec('from ' + app_name + '.models import ' + model_name)
        fields = ''
        for i in eval(model_name + '._meta.fields'):
            fields += "'" + i.name + "', "
        fields = fields.strip(', ')

        table_template = u"""class ${model_name}Table(tables.Table):

    myurl = reverse_lazy('${app_name}:${model_name}_list')
    accao = tables.Column(empty_values=(), verbose_name='Accao')

    class Meta:
        model = ${model_name}
        orderable = False
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class': 'table table-striped table-bordered table-hover'}

        fields = (${fields})

    def render_id(self, record):
        return format_html('<b><a href="{}" >#{}</a></b>', reverse('${app_name}:${model_name}_edit', kwargs={'id': record.id}), record.id)
        #return format_html('<b><a href="#" >Edit</a></b>')

    def render_accao(self, record):
        return format_html('<a href="#" class ="btn btn-primary">Dummy button</a>')"""
        src = Template( table_template )

        d={ 'app_name': app_name, 'model_name': model_name, 'fields': fields}
        file_content = src.substitute(d)
        return file_content


    def create_templates(self, app_name, model_name):
        templates_folder = self.getDjangoProjectPath() + os.sep + app_name + os.sep + 'templates' + os.sep + app_name
        for model in model_name:
            s = self.generate_list_template(app_name, model) + "\n\n"
            self.saveToFile(s, templates_folder + os.sep + model + '_list.html')
            s = self.generate_New_template(app_name, model_name) + "\n\n"
            self.saveToFile(s, templates_folder + os.sep + model + '_new.html')
            s = self.generate_Edit_template(app_name, model_name) + "\n\n"
            self.saveToFile(s, templates_folder + os.sep + model + '_edit.html')

    def create_views(self,app_name, model_name):

        s = """#from __future__ import unicode_literals
#------------------------------
# code generated automagically
#------------------------------
from django.http import HttpResponse
from django_tables2 import RequestConfig
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.core.files import temp as tempfile
from django.utils.html import mark_safe
from django.shortcuts import render
from django.contrib import messages
from django import forms
from django.shortcuts import get_object_or_404\n\n"""

        for model in model_name:
            s += "from .models import " + model + "\n"
            s += "from .tables import " + model + "Table\n"
        s+="\n\n"
        for model in model_name:
            s += self.generateViewList(app_name, model)
            s += self.generateFormModel(app_name, model)
            s += self.generateViewNew(app_name, model)
            s += self.generateViewEdit(app_name, model)

        app_folder = self.getDjangoProjectPath() + os.sep + app_name
        filepath = app_folder + os.sep + 'views.py'
        self.saveOrAppendToFile(s, filepath)

    def create_tables(self, app_name, model_name):
        s = u"""\n\n#------------------------------
# code generated automagically
#------------------------------
import django_tables2 as tables
from django.utils.html import format_html
from django.utils.html import strip_tags
from django.urls import reverse
from django.urls import reverse_lazy
from django.template import defaultfilters
"""

        for model in model_name:
            s += "from .models import " + model + "\n"
        s += "\n\n"
        for model in model_name:
            s += self.generateTable(app_name, model )

        app_folder = self.getDjangoProjectPath() + os.sep + app_name
        filepath = app_folder + os.sep + 'tables.py'
        self.saveOrAppendToFile(s, filepath)

        pass
    """
    def create_template_dirs(self, appname):
        appdir = settings.BASE_DIR + os.sep + str(appname)
        templatesdir = appdir + os.sep + 'templates'
        templates_includedir = templatesdir + os.sep + 'includes'
        templatestagdir = appdir + os.sep + 'templatetags'
        self.createFolder(templatesdir)
        self.create_base_html(templatesdir)

        self.createFolder(templates_includedir)
        self.create_bs4_form_html(templates_includedir)
        self.create_edit_html(templates_includedir)
        self.create_list_html(templates_includedir)
        self.create_new_html(templates_includedir)

        self.createFolder(templatestagdir)
        self.create_ini_py(templatestagdir)
        self.create_templatetag_model_name(templatestagdir)
    """

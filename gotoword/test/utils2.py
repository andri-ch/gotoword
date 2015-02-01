# -*- coding: utf8 -*-

from standalone import models

# Read more:
# https://docs.djangoproject.com/en/1.7/topics/db/models/


class Context(models.StandaloneModel):
    """Keywords have different definitions depending on the context.
    Eg.:
    kivy = Context.objects.create(name="kivy GUI", description="Kivy is an " +
             "OSS library for GUI development suitable for multi-touch apps.")
    """
    name = models.CharField("context name", max_length=50, unique=True)
    description = models.CharField("short description of context",
                                   max_length=100)

    def __unicode__(self):
        return self.name


class Keyword(models.StandaloneModel):
    """
    name - is the keyword itself, like "button", etc; it should be unique
        in DB
    cmd - will be run to obtain info about the keyword, like reading a man
        page,
    info_public - note that exists publicly on the internet and people
        agreed on it
    info - usually an user edited field, this is where the user personalizes
        the definition or adds his own.
    Eg.:
        canvas = Keyword.objects.create(name="canvas")
    """
    name = models.CharField("keyword name", max_length=50, unique=True)
    contexts = models.ManyToManyField(Context, through='Data')
    # this is the source model, it has the ManyToManyField

    #col2 = models.ForeignKey("standalone.MyModel")

    def __unicode__(self):
        "useful when calling print() on a class instance."
        return self.name


class Data(models.StandaloneModel):
    """
    This is the intermediary model for a ManyToMany relationship that shows
    how Keyword is related to Context.
    To create ManyToMany relationships, you need to use this model.
    1. Create a Context and a Keyword:
    Context is the target model of the ManyToManyField from Keyword model;
    Keyword is the source model of the ManyToManyField.
    2. Create the relationship
    >>> r1 = Data(keyword=canvas, context=kivy)
    >>> r1.save()
    # it is possible to let the other kwargs empty when creating a new Data
    # object and add them later on
    >>> r1.info_public = "http://kivy.org/docs/api-kivy.graphics.html#" +
                         "kivy.graphics.Canvas"
    >>> r1.info = "Define a canvas section in which you can add Graphics " +
    ...           "instructions that define how the widget is rendered."
    >>> r1.save()

    info_public(keyword, context)
    info(keyword, context)
    cmd(keyword, context)
    """
    keyword = models.ForeignKey(Keyword)
    context = models.ForeignKey(Context)
    cmd = models.CharField("cmd to run to obtain info", max_length=100)
    info_public = models.TextField("info note publicly available")
    info = models.TextField("note with user's own data")

    def __unicode__(self):
        return self.keyword.name + self.context.name

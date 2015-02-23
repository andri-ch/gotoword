<map version="0.9.0">
<!-- To view this file, download free mind mapping software FreeMind from http://freemind.sourceforge.net -->
<node CREATED="1424514175704" ID="ID_1555171263" MODIFIED="1424514183581" TEXT="HelperSave">
<node CREATED="1424514307504" HGAP="25" ID="ID_1825247075" MODIFIED="1424514612210" POSITION="right" TEXT="EntryState" VSHIFT="-6">
<font NAME="SansSerif" SIZE="12"/>
<node CREATED="1424514696986" HGAP="14" ID="ID_772568698" MODIFIED="1424529242068" TEXT="not kw and not context" VSHIFT="2">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      word doesn't exist into DB, user called &quot;HelperSave&quot;, without specifying the context. Naturally, it should prompt for a context, either from DB or create one on the fly.
    </p>
  </body>
</html>
</richcontent>
<node CREATED="1424514331157" HGAP="49" ID="ID_1552359378" MODIFIED="1424528577975" TEXT="ReadContextState" VSHIFT="-25">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      Prompts user if it wants to choose a context, or leave the default one, or abort.
    </p>
    <p>
      &quot;Do you want to specify a context that this definition of the word applies in?&quot;, \
    </p>
    <p>
      &#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&quot;1. Yes, I will provide a context [1 and press &lt;Enter&gt;]&quot;, \
    </p>
    <p>
      &#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&quot;2. No, I won't provide a context - use the default one [2 and press &lt;Enter&gt;]&quot;, \
    </p>
    <p>
      &#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&quot;3. Abort [3 and press &lt;Enter&gt;]&quot;
    </p>
  </body>
</html>
</richcontent>
<node CREATED="1424515665030" HGAP="21" ID="ID_852949634" MODIFIED="1424528993630" TEXT="1context" VSHIFT="-10">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      user gave a context, but it needs to be checked.
    </p>
  </body>
</html>
</richcontent>
<node CREATED="1424515680117" HGAP="29" ID="ID_1272453029" MODIFIED="1424528751941" TEXT="CheckContextState" VSHIFT="-28">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      Need to check if context exists in DB, otherwise create a new one.
    </p>
  </body>
</html>
</richcontent>
<node CREATED="1424515840759" HGAP="33" ID="ID_1427132368" MODIFIED="1424517189364" TEXT="if context" VSHIFT="-12">
<arrowlink DESTINATION="ID_1364254987" ENDARROW="Default" ENDINCLINATION="488;0;" ID="Arrow_ID_577454641" STARTARROW="None" STARTINCLINATION="488;0;"/>
</node>
<node CREATED="1424515886314" HGAP="33" ID="ID_1121334969" MODIFIED="1424526840913" TEXT="else" VSHIFT="-5">
<arrowlink DESTINATION="ID_1633036748" ENDARROW="Default" ENDINCLINATION="383;0;" ID="Arrow_ID_728362677" STARTARROW="None" STARTINCLINATION="383;0;"/>
</node>
</node>
</node>
<node CREATED="1424515695588" ID="ID_61823590" MODIFIED="1424529250046" TEXT="2 default context">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      user chose the default context - into the DB there's a default context (a placeholder context) used for words that the user doesn't know which context to put them in.
    </p>
  </body>
</html>
</richcontent>
<arrowlink DESTINATION="ID_1364254987" ENDARROW="Default" ENDINCLINATION="282;0;" ID="Arrow_ID_1864138042" STARTARROW="None" STARTINCLINATION="282;0;"/>
</node>
</node>
</node>
<node CREATED="1424514742021" ID="ID_1135413198" MODIFIED="1424528457867" TEXT="not kw and context">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      word doesn't exist in DB, user called &quot;HelperSave a_context&quot; thus specifying the context. App needs to check if it's in the DB.
    </p>
  </body>
</html>
</richcontent>
<node CREATED="1424516987954" HGAP="46" ID="ID_144337783" MODIFIED="1424529053258" TEXT="if ctx" VSHIFT="81">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      if context exists into DB, add the word to DB.
    </p>
  </body>
</html>
</richcontent>
<node CREATED="1424514624802" HGAP="23" ID="ID_1364254987" MODIFIED="1424528852570" TEXT="NewKeywordState" VSHIFT="-34">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      Having a context, add keyword to DB and save/add the user note/definition in this context.
    </p>
  </body>
</html>
</richcontent>
<node CREATED="1424527258625" HGAP="41" ID="ID_1334763674" MODIFIED="1424527355918" TEXT="if not context: context=default_context" VSHIFT="19"/>
</node>
</node>
<node CREATED="1424516995042" HGAP="38" ID="ID_1032685456" MODIFIED="1424529090317" TEXT=" else" VSHIFT="-107">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      if context doesn't exist into DB, create one on the spot.
    </p>
  </body>
</html>
</richcontent>
<node CREATED="1424514827622" HGAP="45" ID="ID_1633036748" MODIFIED="1424527623539" TEXT="CreateContextState" VSHIFT="16">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      if not context in database:
    </p>
    <p>
      &#160;&#160;&#160;CreateContextState
    </p>
  </body>
</html></richcontent>
<node CREATED="1424514941497" HGAP="18" ID="ID_1392954737" MODIFIED="1424527631195" TEXT="if kw" VSHIFT="-12">
<arrowlink DESTINATION="ID_548009505" ENDARROW="Default" ENDINCLINATION="199;0;" ID="Arrow_ID_1578054172" STARTARROW="None" STARTINCLINATION="199;0;"/>
</node>
<node CREATED="1424517111322" HGAP="22" ID="ID_1510490089" MODIFIED="1424527001731" TEXT="else" VSHIFT="13">
<arrowlink DESTINATION="ID_1364254987" ENDARROW="Default" ENDINCLINATION="207;0;" ID="Arrow_ID_1044648585" STARTARROW="None" STARTINCLINATION="207;0;"/>
</node>
</node>
</node>
</node>
<node CREATED="1424514744178" ID="ID_1392791518" MODIFIED="1424529717330" TEXT="kw and not context" VSHIFT="16">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      word exists into DB - the App is aware of that, user called &quot;HelperSave&quot;, without specifying the context -&gt; So update the word to the same context. If word belongs to multiple contexts, it should prompt user to choose the current active context.
    </p>
  </body>
</html>
</richcontent>
<node CREATED="1424515120721" HGAP="75" ID="ID_548009505" MODIFIED="1424529641722" TEXT="UpdateKeywordState" VSHIFT="10">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      it shouldn't test context, because all states that lead to this one have done that already.
    </p>
  </body>
</html>
</richcontent>
<icon BUILTIN="button_cancel"/>
<node CREATED="1424515336878" HGAP="78" ID="ID_768795858" MODIFIED="1424527664391" TEXT="if context" VSHIFT="-73">
<node CREATED="1424515372067" HGAP="33" ID="ID_597853387" MODIFIED="1424527558913" TEXT="if not ctx" VSHIFT="-21">
<arrowlink DESTINATION="ID_1633036748" ENDARROW="Default" ENDINCLINATION="144;0;" ID="Arrow_ID_483279626" STARTARROW="None" STARTINCLINATION="144;0;"/>
</node>
</node>
</node>
</node>
<node CREATED="1424514746343" HGAP="21" ID="ID_1346780156" MODIFIED="1424529640851" TEXT="kw and context" VSHIFT="11">
<richcontent TYPE="NOTE"><html>
  <head>
    
  </head>
  <body>
    <p>
      word exists in DB - the App is aware of that, user called &quot;HelperSave a_context&quot; thus specifying the context -&gt; update the word to same context. This state is useless if there's another state that forces user to choose the default context.
    </p>
  </body>
</html>
</richcontent>
<arrowlink DESTINATION="ID_548009505" ENDARROW="Default" ENDINCLINATION="205;0;" ID="Arrow_ID_578223759" STARTARROW="None" STARTINCLINATION="205;0;"/>
<icon BUILTIN="button_cancel"/>
</node>
</node>
</node>
</map>

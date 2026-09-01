<?xml version="1.0" encoding="UTF-8"?>
<!--
    tei2html.xsl — builds a plain static HTML page for GitHub Pages
    from the TEI edition of "Ten Great Novels".

    Usage:  xsltproc -o index.html tei2html.xsl Ten_Great_Novels_1884.xml
    XSLT 1.0; runs with xsltproc, Saxon and in the browser.
-->
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:tei="http://www.tei-c.org/ns/1.0"
                exclude-result-prefixes="tei">

  <xsl:output method="html" encoding="UTF-8" indent="yes"
              doctype-system="about:legacy-compat"/>
  <xsl:strip-space elements="tei:div tei:list tei:titlePage tei:docImprint tei:address"/>

  <!-- Set by build.sh: the Wikidata Query Service link for the map of the
       correspondents' places, and the mirrored query file in this repository.
       If the URL is empty the footer line is left out. -->
  <xsl:param name="wdqs-url"/>
  <xsl:param name="graphml-file">ten-great-novels.graphml</xsl:param>
  <xsl:param name="geojson-url"/>

  <!-- The URL of this edition comes from <idno type="URL"> in the header; the
       parameter only overrides it (e.g. for a preview build). -->
  <xsl:param name="edition-url"/>
  <xsl:variable name="url">
    <xsl:choose>
      <xsl:when test="$edition-url != ''"><xsl:value-of select="$edition-url"/></xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="normalize-space(//tei:publicationStmt/tei:idno[@type='URL'][1])"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="orcid"
      select="//tei:titleStmt/tei:respStmt/tei:persName[contains(@ref,'orcid.org')][1]/@ref"/>
  <xsl:variable name="licence" select="//tei:publicationStmt/tei:availability/tei:licence[1]"/>

  <!-- Muenchian grouping: XSLT 1.0 has no distinct-values(), so a title counts
       once if it is the first element in its @ref group. -->
  <xsl:key name="novel-by-ref" match="tei:rs[@type='novel'][@ref]" use="@ref"/>
  <xsl:key name="ranked-by-ref"
           match="tei:div[@type='vote']//tei:rs[@type='novel'][@ref]" use="@ref"/>

  <!-- Google Books identifier, taken from the header so that the page
       numbers link to the facsimile. Falls back to the Chicago copy. -->
  <xsl:variable name="gb-raw"
                select="/tei:TEI/tei:teiHeader//tei:ref[contains(@target,'books.google.com')][1]/@target"/>
  <xsl:variable name="gb-id">
    <xsl:choose>
      <xsl:when test="contains($gb-raw,'id=')">
        <xsl:variable name="tail" select="substring-after($gb-raw,'id=')"/>
        <xsl:choose>
          <xsl:when test="contains($tail,'&amp;')"><xsl:value-of select="substring-before($tail,'&amp;')"/></xsl:when>
          <xsl:otherwise><xsl:value-of select="$tail"/></xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>a5xPAQAAMAAJ</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <!-- ===================================================================== -->
  <!--  Page frame                                                           -->
  <!-- ===================================================================== -->

  <xsl:template match="/">
    <html lang="en">
      <head>
        <!-- The character set is declared by the HTML serialiser itself
             (<meta http-equiv="Content-Type" …>); a second one here would
             be a validation error. -->
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <xsl:if test="$licence/@target">
          <link rel="license" href="{$licence/@target}"/>
        </xsl:if>
        <title><xsl:value-of select="//tei:titleStmt/tei:title[@type='main']"/></title>
        <style>
:root{
  color-scheme: light;
  --fg:#24292f; --bg:#ffffff; --muted:#6a737d; --rule:#e6e8eb; --panel:#f6f8fa;
  --vote:#a4243b; --mention:#8a6a72;
  --author:#2559a8; --voter:#17796a; --place:#7b3fa0; --page:#a86800;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  font-size:1rem;line-height:1.65;-webkit-text-size-adjust:100%}
main{max-width:42rem;margin:0 auto;padding:2rem 1.1rem 4rem;overflow-wrap:break-word}
h1{font-size:1.4rem;margin:0 0 .4rem}
h2{font-size:1.05rem;margin:2.4rem 0 .8rem}
h3{font-size:1rem;font-weight:600;color:var(--muted);margin:1.6rem 0 .5rem}
p{margin:0 0 1rem}
a{color:inherit}
.box{border:1px solid var(--rule);border-radius:4px;padding:.85rem 1rem;
  margin:0 0 .7rem;font-size:.95rem;line-height:1.8;background:var(--panel)}
.box .bh{display:block;font-weight:600;color:var(--fg);margin-bottom:.1rem}
.box b{font-weight:600}
.box .note{color:var(--muted);font-size:.9em}
.box-about{border-left:3px solid #55705f}
.box-about p{margin:.35rem 0 0}
.box-about a{text-decoration:underline}
.box-cite{border-left:3px solid #6a737d}
.box-read{border-left:3px solid #24292f}
.box-data{border-left:3px solid #41627e}
.box-stats{border-left:3px solid #7a5a3c;margin-bottom:2.2rem}
.box-cite a,.box-data a{text-decoration:underline}
.box-data ul{margin:.1rem 0 0;padding-left:1.2rem}
.box-data li{margin:.1rem 0}
.titlepage{border-bottom:1px solid var(--rule);padding-bottom:1.4rem;margin-bottom:1.6rem}
.titlepage p{margin:0 0 .3rem;color:var(--muted);font-size:.95rem}
.titlepage .imprint{font-size:.9rem;line-height:1.5;margin-top:.8rem}
.dateline{color:var(--muted)}
.closer{margin-top:1rem}
ul,ol{margin:0 0 1.2rem;padding-left:1.4rem}
li{margin:.2rem 0}
.vote{list-style:none;padding-left:0}
.num{color:var(--muted);font-size:.9em}
.response{margin:0 0 1.6rem;padding-top:1.2rem;border-top:1px solid var(--rule)}
.org{font-style:italic}
.novel{color:var(--vote)}
.novel[data-ana="#mention"]{color:var(--mention)}
.author{color:var(--author)}
.voter,.pers{color:var(--voter)}
.place{color:var(--place)}
a.novel,a.author,a.pers,a.place{text-decoration:none}
a.novel:hover,a.author:hover,a.pers:hover,a.place:hover{text-decoration:underline}
.unsure{border-bottom:1px dotted currentColor}
.misattributed{border-bottom:1px dashed currentColor}
h3.ital{font-style:italic}
ul.cols{columns:2;column-gap:1.6rem}
ul.cols li{break-inside:avoid}
@media (max-width:30rem){ul.cols{columns:1}}
.pb{display:inline;white-space:nowrap;color:var(--page);font-size:.85em;
  font-style:normal;text-decoration:none;padding:0 .15em}
.pb:hover{text-decoration:underline}
        </style>
      </head>
      <body>
        <main>
          <xsl:call-template name="about"/>
          <xsl:call-template name="citation"/>
          <xsl:call-template name="legend"/>
          <xsl:call-template name="data"/>
          <xsl:call-template name="statistics"/>
          <xsl:apply-templates select="tei:TEI/tei:text"/>
        </main>
      </body>
    </html>
  </xsl:template>

  <xsl:template name="about">
    <div class="box box-about">
      <span class="bh">About this edition</span>
      <p>In 1884, Jenkin Lloyd Jones invited friends and members of his Unitarian circle to name
        the "ten great novels" they would recommend to young readers. A preliminary ranking
        appeared in "Unity" on
        <a href="https://books.google.com/books?id=zzUrAAAAYAAJ&amp;pg=PA205">16 July 1884</a>,
        followed by an expanded version on
        <a href="https://books.google.com/books?id=zzUrAAAAYAAJ&amp;pg=PA484">16 February 1885</a>.
        The correspondence was subsequently reissued as a standalone pamphlet. This digital
        edition presents the pamphlet in full, with novels, authors, correspondents, and places
        annotated and, where possible, linked to Wikidata. Extracted data derived from the edition
        are also provided for further analysis and reuse.</p>
    </div>
  </xsl:template>

  <xsl:template name="citation">
    <p class="box box-cite">
      <span class="bh">How to cite this page</span>
      <xsl:text>Jenkin Lloyd Jones: </xsl:text>
      <b>Ten Great Novels: Suggestions for Clubs and Private Reading.</b>
      <xsl:text> Seventh Thousand. Chicago: Kerr &amp; Company 1891. TEI edition, digitized, encoded and annotated by </xsl:text>
      <a href="{$orcid}">Frank Fischer</a>
      <xsl:text>, version 1.0, 31 August 2026, </xsl:text>
      <a href="{$url}"><xsl:value-of select="$url"/></a>
      <xsl:text>.</xsl:text>
      <xsl:if test="$licence">
        <xsl:text> </xsl:text>
        <span class="note"><xsl:call-template name="licence-text"/></span>
      </xsl:if>
    </p>
  </xsl:template>

  <!-- The licence sentence is taken verbatim from <licence>. Only its name is
       linked to @target; if that name does not occur in the text, the whole
       sentence becomes the link. -->
  <xsl:template name="licence-text">
    <xsl:variable name="txt" select="normalize-space($licence)"/>
    <xsl:variable name="name">CC0 1.0 Universal</xsl:variable>
    <xsl:choose>
      <xsl:when test="contains($txt,$name)">
        <xsl:value-of select="substring-before($txt,$name)"/>
        <a href="{$licence/@target}"><xsl:value-of select="$name"/></a>
        <xsl:value-of select="substring-after($txt,$name)"/>
      </xsl:when>
      <xsl:otherwise>
        <a href="{$licence/@target}"><xsl:value-of select="$txt"/></a>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="legend">
    <p class="box box-read">
      <span class="bh">How to read this edition</span>
      Colour marks the annotation:
      <b class="novel">novel (vote)</b> &#183;
      <b class="novel" data-ana="#mention">novel (mentioned only)</b> &#183;
      <b class="author">author</b> &#183;
      <b class="voter">correspondent</b> &#183;
      <b class="place">place</b>.
      <b class="pb">[page&#160;n:]</b> marks a page break in the original and links to the facsimile.
      <span class="note">Coloured names link to their Wikidata record; a dotted underline marks an uncertain or missing identification. Please note that, in some cases, the votes recorded in the letters do not add up to the totals given in the list at the beginning.</span>
    </p>
  </xsl:template>

  <xsl:template name="data">
    <div class="box box-data">
      <span class="bh">Data and downloads</span>
      <ul>
        <li>Bipartite network of correspondents and votes
          (<a href="{$graphml-file}">GraphML</a>)</li>
        <li>Places of the correspondents in
          <a href="{$wdqs-url}">Wikidata Query Service</a><xsl:if test="$geojson-url != ''"> or
          <a href="{$geojson-url}">GeoJSON</a></xsl:if></li>
      </ul>
    </div>
  </xsl:template>

  <!-- All figures are counted from the TEI file at build time. -->
  <xsl:template name="statistics">
    <p class="box box-stats">
      <span class="bh">The edition in numbers</span>
      <xsl:value-of select="count(//tei:div[@type='response'])"/> letters &#183;
      <xsl:value-of select="count(//tei:rs[@type='novel'][@ana='#vote'])"/> votes &#183;
      <xsl:value-of select="count(//tei:rs[@type='novel'][@ana='#mention'])"/> mentions &#183;
      <xsl:value-of select="count(//tei:rs[@type='novel'][@ref][generate-id() = generate-id(key('novel-by-ref',@ref)[1])])"/> distinct novels &#183;
      <xsl:value-of select="count(//tei:div[@type='vote']//tei:rs[@type='novel'][@ref][generate-id() = generate-id(key('ranked-by-ref',@ref)[1])])"/> novels in the printed ranking
    </p>
  </xsl:template>

  <!-- ===================================================================== -->
  <!--  Structure                                                            -->
  <!-- ===================================================================== -->

  <xsl:template match="tei:teiHeader"/>

  <xsl:template match="tei:titlePage">
    <div class="titlepage">
      <h1><xsl:value-of select="tei:docTitle/tei:titlePart[@type='main']"/></h1>
      <p><xsl:value-of select="tei:docTitle/tei:titlePart[@type='sub']"/></p>
      <p><xsl:apply-templates select="tei:byline/node()"/></p>
      <p><xsl:value-of select="tei:docEdition"/></p>
      <p class="imprint"><xsl:apply-templates select="tei:docImprint"/></p>
    </div>
  </xsl:template>

  <xsl:template match="tei:docImprint">
    <xsl:for-each select="tei:pubPlace|tei:publisher|tei:address/tei:addrLine|tei:docDate">
      <xsl:apply-templates/>
      <xsl:if test="position() != last()"><xsl:text> </xsl:text><br/></xsl:if>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="tei:body/tei:head">
    <h1><xsl:apply-templates/></h1>
  </xsl:template>

  <xsl:template match="tei:head">
    <h2><xsl:apply-templates/></h2>
  </xsl:template>

  <xsl:template match="tei:div[@type='votegroup']/tei:head">
    <h3>
      <xsl:if test="@rend='italic'"><xsl:attribute name="class">ital</xsl:attribute></xsl:if>
      <xsl:apply-templates/>
    </h3>
  </xsl:template>

  <!-- Circular letter: dateline, then salutation and text in one paragraph -->
  <xsl:template match="tei:div[@type='question']">
    <div class="question">
      <xsl:apply-templates select="tei:head"/>
      <p class="dateline"><xsl:apply-templates select="tei:opener/tei:dateline/node()"/></p>
      <p>
        <xsl:apply-templates select="tei:opener/tei:salute"/>
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="tei:p/node()"/>
      </p>
      <xsl:apply-templates select="tei:closer"/>
    </div>
  </xsl:template>

  <!-- Reply: heading and first paragraph run on in one line, as in print -->
  <xsl:template match="tei:div[@type='response']">
    <div class="response" id="letter-{@n}">
      <p>
        <xsl:apply-templates
            select="node()[count(following-sibling::tei:p) = count(../tei:p)]"/>
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="tei:p[1]/node()"/>
      </p>
      <xsl:apply-templates select="tei:p[1]/following-sibling::node()"/>
    </div>
  </xsl:template>

  <xsl:template match="tei:opener|tei:closer">
    <xsl:choose>
      <xsl:when test="parent::tei:div[@type='response']"><xsl:apply-templates/></xsl:when>
      <xsl:otherwise><p class="closer"><xsl:apply-templates/></p></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:p"><p><xsl:apply-templates/></p></xsl:template>
  <xsl:template match="tei:list">
    <ul>
      <xsl:attribute name="class">
        <xsl:text>vote</xsl:text>
        <xsl:if test="@rend='two-column'"> cols</xsl:if>
      </xsl:attribute>
      <xsl:apply-templates/>
    </ul>
  </xsl:template>
  <xsl:template match="tei:list[@type='ordered']"><ol><xsl:apply-templates/></ol></xsl:template>
  <xsl:template match="tei:item"><li><xsl:apply-templates/></li></xsl:template>
  <xsl:template match="tei:num"><span class="num"><xsl:apply-templates/></span></xsl:template>
  <xsl:template match="tei:hi[@rend='italic']|tei:foreign|tei:title"><em><xsl:apply-templates/></em></xsl:template>
  <xsl:template match="tei:orgName"><span class="org"><xsl:apply-templates/></span></xsl:template>
  <xsl:template match="tei:dateline|tei:salute|tei:date"><xsl:apply-templates/></xsl:template>

  <!-- ===================================================================== -->
  <!--  Page breaks: [page n:] linked to the facsimile                        -->
  <!-- ===================================================================== -->

  <xsl:template match="tei:pb">
    <a class="pb" id="page-{@n}" title="Page {@n} in the facsimile">
      <xsl:attribute name="href">
        <xsl:text>https://books.google.com/books?id=</xsl:text>
        <xsl:value-of select="$gb-id"/>
        <xsl:text>&amp;pg=PA</xsl:text>
        <xsl:value-of select="@n"/>
      </xsl:attribute>
      <xsl:text>[page </xsl:text><xsl:value-of select="@n"/><xsl:text>:]</xsl:text>
    </a>
    <xsl:text> </xsl:text>
  </xsl:template>

  <!-- ===================================================================== -->
  <!--  Annotated entities                                                   -->
  <!-- ===================================================================== -->

  <!-- Works and authors: the whole reference becomes clickable -->
  <xsl:template match="tei:rs[@type='novel' or @type='author']">
    <xsl:variable name="cls">
      <xsl:value-of select="@type"/>
      <xsl:if test="@cert"> unsure</xsl:if>
      <xsl:if test="@subtype='misattributed'"> misattributed</xsl:if>
    </xsl:variable>
    <xsl:choose>
      <!-- Title running across a page break: two anchors around the page
           marker, so that no nested links are produced -->
      <xsl:when test="@ref and tei:pb">
        <a class="{$cls}" href="{@ref}">
          <xsl:call-template name="rs-atts"/>
          <xsl:apply-templates select="node()[following-sibling::tei:pb]"/>
        </a>
        <xsl:apply-templates select="tei:pb"/>
        <a class="{$cls}" href="{@ref}">
          <xsl:call-template name="rs-atts"/>
          <xsl:apply-templates select="node()[not(self::tei:pb)][not(following-sibling::tei:pb)]"/>
        </a>
      </xsl:when>
      <xsl:when test="@ref">
        <a class="{$cls}" href="{@ref}">
          <xsl:call-template name="rs-atts"/>
          <xsl:apply-templates/>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <span class="{$cls}">
          <xsl:call-template name="rs-atts"/>
          <xsl:apply-templates/>
        </span>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="rs-atts">
    <xsl:if test="@ana"><xsl:attribute name="data-ana"><xsl:value-of select="@ana"/></xsl:attribute></xsl:if>
    <xsl:choose>
      <xsl:when test="@subtype='misattributed'">
        <xsl:attribute name="title">Misattributed in the source; the link points to the author the work is actually by</xsl:attribute>
      </xsl:when>
      <xsl:when test="@cert">
        <xsl:attribute name="title">Uncertain identification (cert="<xsl:value-of select="@cert"/>")</xsl:attribute>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <!-- Correspondents: name and place are linked separately, so that no
       nested links are produced -->
  <xsl:template match="tei:rs[@type='voter']">
    <span class="voter"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:rs[@type='voter']/tei:persName">
    <xsl:choose>
      <xsl:when test="../@ref">
        <a class="pers" href="{../@ref}"><xsl:apply-templates/></a>
      </xsl:when>
      <!-- no Wikidata record: marked like an uncertain identification -->
      <xsl:otherwise>
        <span class="pers unsure" title="No Wikidata record"><xsl:apply-templates/></span>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:placeName">
    <xsl:choose>
      <xsl:when test="@ref"><a class="place" href="{@ref}"><xsl:apply-templates/></a></xsl:when>
      <xsl:otherwise><span class="place"><xsl:apply-templates/></span></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:persName">
    <xsl:choose>
      <xsl:when test="@ref"><a class="pers" href="{@ref}"><xsl:apply-templates/></a></xsl:when>
      <xsl:otherwise><xsl:apply-templates/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>

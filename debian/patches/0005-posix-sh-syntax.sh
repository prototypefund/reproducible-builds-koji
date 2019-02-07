--- a/plugins/Makefile
+++ b/plugins/Makefile
@@ -29,7 +29,7 @@
 		echo "ERROR: A destdir is required"; \
 		exit 1; \
 	fi
-	if [ "$(PYTHON)" == "python" ] ; then \
+	if [ "$(PYTHON)" = "python" ] ; then \
 		mkdir -p $(DESTDIR)/$(HUBPLUGINDIR); \
 		mkdir -p $(DESTDIR)/$(BUILDERPLUGINDIR); \
 		install -p -m 644 $(HUBFILES) $(DESTDIR)/$(HUBPLUGINDIR); \

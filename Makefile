


push:
	@read -p "Commit izohini kiriting: " m; \
	git add . ; \
	git commit -m "$$m"; \
	git push
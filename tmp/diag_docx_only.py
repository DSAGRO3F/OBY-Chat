#cat > /tmp/diag_docx_only.py << 'PY'
import os, resource, time
from src.func.retrieve_relevant_chunks import retrieve_relevant_chunks

def rss_mb():
    # macOS: ru_maxrss en bytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024*1024)

print(f"[MEM] start rss_mb={rss_mb():.1f}")
q = "chute personne âgée"
try:
    # DOCX seulement: k_docx=1, k_web=0
    out = retrieve_relevant_chunks(q, top_k_docx=1, top_k_web=0)
    print("[OK] retrieve DOCX only")
except Exception as e:
    print("[ERR] retrieve DOCX only:", e)
print(f"[MEM] end   rss_mb={rss_mb():.1f}")
print("---- OUTPUT PREVIEW ----")
print(out[:400])
#PY
# Legal form chunks v1 — bàn giao Phase 1

Gói này là bản lọc nguyên dòng từ published snapshot, phục vụ tham khảo nội dung cho Agentic Document Generation. Không chứa raw DOCX, embedding, dữ liệu điền mẫu hoặc nội dung do LLM sinh. Không có kết luận mới về hiệu lực pháp luật và không cấp production data gate PASS.

## Dữ liệu và phạm vi

- `form_chunks.jsonl`: 212 chunks, chỉ `content_kind == "form"`; 185 unique `provision_id`, 15 `doc_id`, 79 `source_id` (72 DOCX, 6 PDF, 1 HTML). Đây là số logical provisions trong snapshot, **không phải 185 biểu mẫu pháp lý đã deduplicate**.
- `annex_chunks.jsonl`: 131 chunks, chỉ `content_kind == "annex"`; 72 provisions, 21 `doc_id`, 33 sources. Không trộn vào form JSONL.
- `manifest.json`: phiên bản schema, timestamp, commits, hashes, counts và limitations.
- `source_registry.json`: 101 source records được tham chiếu bởi hai JSONL; mỗi record giữ nguyên giá trị trong published `data/registry/sources.json`.
- `document_registry.json`: 21 document records liên quan, giữ nguyên giá trị từ published registry. `source_ids` có thể bao gồm nguồn khác không nằm trong registry rút gọn; chỉ các nguồn trực tiếp được chunk tham chiếu mới được đóng gói.
- `audit.json`: inventory mọi provision, chunk IDs/thứ tự dòng nguồn, phân loại annex, danh sách thiếu metadata, kiểm hash 101 file nguồn và ba mẫu kiểm cấu trúc bảng DOCX.
- `FORM_CATALOG.md`: danh sách đầy đủ 185 logical form provisions theo văn bản, kèm trích đoạn đầu mẫu, IDs, số chunks/fragments và đường dẫn nguồn.
- `SHA256SUMS.txt`: SHA256 của các file trong folder bàn giao (không tự chứa hash của chính file checksum).

## Những văn bản đã có biểu mẫu được chunk

Danh sách dưới đây lấy trực tiếp từ `doc_number` và `content_kind` trong JSONL, không phải cam kết đủ mọi mẫu ban hành kèm văn bản. “Provisions” là số `provision_id` riêng biệt, có thể bao gồm mẫu lặp từ full document và standalone DOCX. Xem [catalog từng mẫu](FORM_CATALOG.md) để tra IDs, trích đoạn và nguồn, và [audit](audit.json) để tra các thiếu sót theo chunk.

- **Thông tư 09/2020/TT-BLĐTBXH**: 6 form chunks, 6 provisions, 6 nguồn — mẫu liên quan sử dụng lao động chưa thành niên.
- **Thông tư 11/2022/TT-BLĐTBXH**: 10 form chunks, 5 provisions, 4 nguồn — phiếu thông tin tuyển dụng, người tìm việc và người lao động.
- **Nghị định 104/2022/NĐ-CP**: 1 form chunk, 1 provision, 1 nguồn — giấy đề nghị vay vốn hỗ trợ tạo việc làm.
- **Nghị định 145/2020/NĐ-CP**: 20 form chunks, 19 provisions, 19 nguồn — các mẫu lao động thuộc nhiều phụ lục; cần giữ namespace phụ lục/nguồn.
- **Nghị định 146/2018/NĐ-CP**: 15 form chunks, 11 provisions, 1 nguồn — các mẫu bảo hiểm y tế; có nội dung dạng index và fragments cần đối chiếu nguồn.
- **Nghị định 152/2020/NĐ-CP**: 20 form chunks, 19 provisions, 19 nguồn — các mẫu sử dụng lao động nước ngoài.
- **Nghị định 158/2025/NĐ-CP**: 1 form chunk, 1 provision, 1 nguồn — giấy xác nhận thời gian hợp tác lao động để giải quyết chế độ BHXH.
- **Nghị định 188/2025/NĐ-CP**: 18 form chunks, 12 provisions, 2 nguồn — các mẫu bảo hiểm y tế; có nguồn full DOCX và PDF.
- **Nghị định 219/2025/NĐ-CP**: 6 form chunks, 4 provisions, 1 nguồn — các mẫu giấy phép/xác nhận liên quan lao động nước ngoài.
- **Quyết định 23/2021/QĐ-TTg**: 20 form chunks, 20 provisions, 1 nguồn — các mẫu đề nghị/hỗ trợ người lao động và người sử dụng lao động.
- **Nghị định 374/2025/NĐ-CP**: 48 form chunks, 46 provisions, 1 nguồn — các mẫu việc làm, trợ cấp và hỗ trợ đào tạo; một số trích đoạn mở đầu bị tách/flatten, cần xem full source.
- **Nghị định 61/2020/NĐ-CP**: 4 form chunks, 4 provisions, 1 nguồn — các mẫu liên quan trợ cấp thất nghiệp/hỗ trợ học nghề.
- **Nghị định 70/2023/NĐ-CP**: 7 form chunks, 6 provisions, 6 nguồn — các mẫu sử dụng lao động nước ngoài.
- **Nghị định 75/2023/NĐ-CP**: 6 form chunks, 3 provisions, 1 nguồn — các mẫu khám/chuyển tuyến/hợp đồng bảo hiểm y tế.
- **Nghị định 88/2020/NĐ-CP**: 30 form chunks, 28 provisions, 15 nguồn — các mẫu hỗ trợ từ quỹ bảo hiểm tai nạn lao động, bệnh nghề nghiệp.

Ngoài các văn bản trên, `annex_chunks.jsonl` còn có **6 văn bản chỉ xuất hiện ở nhóm annex**: Thông tư 10/2020/TT-BLĐTBXH (8 chunks), Nghị định 135/2020/NĐ-CP (10), Nghị định 293/2025/NĐ-CP (6), Nghị định 39/2016/NĐ-CP (26), Nghị định 74/2024/NĐ-CP (4), Luật 97/2015/QH13 (10). Đặc biệt, Nghị định 39/2016 có annex mang tiêu đề biểu mẫu dù nhãn gốc vẫn là `annex`; chúng không được chuyển sang form JSONL. Annex chunks của 15 văn bản có form cũng nằm trong file annex riêng. Tổng cả gói là 21 văn bản.

## Các vấn đề tồn đọng cần xử lý ở task riêng

- **Table/layout fidelity**: `STRUCTURAL_FIDELITY_LIMITATION`; không thể tái tạo DOCX chính xác chỉ từ text chunks. Cần dùng DOCX gốc và đối chiếu layout trước khi render văn bản thực tế.
- **Fragment boundaries**: 35 form fragments thiếu index/offset; có chunk chứa index/tên mẫu hoặc phần tiêu đề bị flatten. Giữ nguyên dòng và source order; chưa chứng nhận ghép lại được full template.
- **Provenance tới DOCX**: 82 form chunks lấy trực tiếp từ PDF/HTML; chưa chứng nhận ánh xạ từng chunk sang DOCX tương đương. 130 form chunks thiếu URL nhưng còn path/hash/locator. Không tự dựng URL hoặc gán nguồn khác.
- **Legal metadata**: 59 form chunks có năm issued date khác năm trong số hiệu; 119 có `valid_from=2020-01-01`. Tất cả 101 source records vẫn `pending` trong khi chunks ghi `verified`. Các giá trị đã giữ nguyên; cần legal metadata review riêng trước khi dùng để kết luận hiệu lực.
- **Duplicate/coverage**: 185 provisions chưa phải danh sách biểu mẫu pháp lý đã deduplicate; có 18 nhóm trùng content hash. Chưa kiểm đủ mọi mẫu của từng văn bản, chưa sửa nhãn annex/form và chưa nghiệm thu legal applicability năm 2026.
- **Annex classification**: 23 annex provisions còn `NEEDS_REVIEW`; nhãn mô tả của các annex khác cũng không thay legal review.
- **Release metadata**: embedded candidate ID khác published container ID, được manifest giải thích; không sửa record. Phase 1 closeout vẫn OPEN / NOT SIGNED OFF, không mở lại các vấn đề ngoài phạm vi export.

UTF-8 JSONL, một JSON object mỗi dòng, chunk schema v2. Giữ nguyên toàn bộ fields và bytes của từng dòng nguồn, kể cả các field ngoài danh sách dưới đây. Thứ tự là thứ tự dòng vật lý trong source JSONL; không sắp xếp theo tên mẫu hay UUID.

Các field chính:

- `chunk_id`: định danh chunk; `content`, `content_hash` (SHA256 của `content.encode("utf-8")`), `content_length`.
- `doc_id`, `doc_number`, `doc_title`, `doc_type`: định danh văn bản theo snapshot.
- `provision_id`: logical provision, đã có namespace văn bản và đôi khi source; `provision_version_id`: phiên bản của provision; `structural_path`: mảng locator cấu trúc.
- `source_refs`: danh sách `{source_id, locator, source_url}`; dùng `source_id` để tra registry, không dùng tên `Mẫu số 01` làm khóa.
- `content_kind`: loại đã gán trong snapshot; `is_fragment`: dấu hiệu chunk chỉ là một phần. Các field `parent_id`, `clause_numbers`, v.v. cũng được giữ nguyên.
- `release_id`, `verification_status`, `issued_date`, `valid_from`, `valid_to`: metadata nguyên bản, không phải chứng nhận mới của exporter.

## Nguồn và hashes

Published container: `phase1-febf5129f0e33d40`. Active pointer đã được xác minh trước và sau export.

- Manifest nguồn SHA256: `ef0c1688a72500c16958c5fcdeafd1893adc998db2cdfdabb8cd344b99e9d4ac`.
- Chunks nguồn SHA256: `6216af1cee83efc1d1963f8b8202ebe5efd2fab25dc4b6655b4a2ef965144f1f`.
- Form JSONL SHA256: `94a91fc0eaa655aa281efb5aa02a038f293b34a0674100b9739d2a073069f1be`.
- Annex JSONL SHA256: `d89de7b1f8591032905089f3082088aba49776d49187e4019aacd21349e1ea1f`.

Đường dẫn chunks tương đối với published container: `data/staging/phase1-candidate/chunks.jsonl`. Cả 113 snapshot files khớp `snapshot_file_sha256`. Snapshot có 3.110 chunks: 2.767 normative, 212 form, 131 annex; manifest ghi 61 parsed documents.

**Embedded `release_id` của tất cả chunks là `candidate-febf5129f0e33d40`.** Export giữ nguyên field này. `manifest.source_release_id` xác định container published; suffix của hai IDs khớp. Không diễn giải khác biệt này thành dữ liệu thuộc release khác hoặc tự sửa IDs.

Manifest nguồn ghi `gate1=PASS`, `verified_as_of=2026-09-17`; đây là metadata lịch sử. Current session state ghi Phase 1 closeout OPEN / P1R-06 NOT SIGNED OFF. Những giá trị lịch sử không phải acceptance cho export hoặc xác nhận luật còn hiệu lực ngày tạo văn bản năm 2026.

## Đọc và truy vết bằng Python

Chạy từ thư mục gói bàn giao, chỉ cần Python stdlib:

```python
from collections import defaultdict
import hashlib
import json
from pathlib import Path

package = Path.cwd()
manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
registry = {
    s["source_id"]: s
    for s in json.loads((package / "source_registry.json").read_text(encoding="utf-8"))
}
data = (package / "form_chunks.jsonl").read_bytes()
assert hashlib.sha256(data).hexdigest() == manifest["files"]["form_chunks.jsonl"]["sha256"]

groups = defaultdict(list)
for line in data.decode("utf-8").splitlines():
    chunk = json.loads(line)
    assert chunk["content_kind"] == "form"
    assert hashlib.sha256(chunk["content"].encode("utf-8")).hexdigest() == chunk["content_hash"]
    key = (chunk["provision_id"], chunk["provision_version_id"], tuple(chunk["structural_path"]))
    groups[key].append(chunk)  # Giữ thứ tự gặp trong file.
    for ref in chunk["source_refs"]:
        source = registry[ref["source_id"]]
        print(chunk["chunk_id"], source["path"], source["sha256"], ref["locator"])
```

`source.path` là đường dẫn tương đối với **source repository**, không phải thư mục gói. Với raw corpus đã bàn giao, tìm đúng file theo path hoặc hash; kiểm SHA256 của bytes DOCX trùng `source.sha256`, rồi dùng `source_refs[].locator` để định vị đoạn/bảng/hàng. Nếu đồng nghiệp đã đổi tên file, dùng hash để đối chiếu, không đoán theo tên mẫu. `source_id` là khóa registry, không mặc định suffix của nó là hash nội dung file.

130/212 form chunks không có URL ở ref hoặc registry; path/hash và locator vẫn có. Không dựng URL thay thế. 130 form chunks có direct DOCX provenance; **82 form chunks chỉ có PDF/HTML provenance**, chưa có ánh xạ chính xác về DOCX đã chứng nhận. Có thể dùng `doc_id` tra `document_registry.json` và registry đầy đủ của snapshot để tìm DOCX cùng văn bản, nhưng đó chỉ là contextual alternative; phải đối chiếu nội dung/hash/locator trước khi coi là cùng template. Không gán DOCX khác làm nguồn thật của chunk.

## Form, annex và fragments

`form_chunks.jsonl` chỉ dùng đúng nhãn `form`; không lọc bằng chuỗi “Mẫu số”. Annex có thể là biểu mẫu, danh mục hoặc nội dung quy phạm/tham khảo. `audit.provision_inventory` ghi category, heading evidence và từng chunk thuộc mỗi annex:

- `FORM`: 23 annex provisions có tiêu đề biểu mẫu rõ, ví dụ mẫu báo cáo/biên bản NĐ 39/2016, hợp đồng liên kết đào tạo tại NĐ 374/2025. Vẫn nằm trong annex JSONL.
- `CATALOG`: 17 provisions, ví dụ danh mục công việc TT 09/2020, TT 10/2020, phí/lệ phí Luật 97/2015.
- `APPLICATION_LIST`: 3 provisions về địa bàn áp dụng mức lương tối thiểu NĐ 74/2024 và NĐ 293/2025.
- `OTHER_NORMATIVE_OR_REFERENCE`: 6 provisions về lộ trình/tuổi nghỉ hưu, công việc khai thác than NĐ 135/2020; nhãn mô tả nội dung, không phải legal acceptance.
- `NEEDS_REVIEW`: 23 provisions chưa xác định chắc, có index tập mẫu, nội dung hỗn hợp hoặc tiêu đề chưa đủ. Không tự nâng thành biểu mẫu.

Tên và structural item có thể lặp giữa văn bản hoặc giữa standalone source và full document. Gom bằng `provision_id` + `provision_version_id`; đối chiếu `structural_path` và nguồn. Không gộp chỉ bằng tên hiển thị hoặc số mẫu.

Có 35 form chunks đánh dấu `is_fragment=true`, thuộc 22 provisions; 23 provisions có nhiều chunk (một số nhóm có cả chunk không đánh dấu fragment). Annex có 52 fragment chunks. Snapshot **không có fragment index hay character offsets**. Inventory lưu source line numbers và chunk IDs theo thứ tự nguồn; giữ thứ tự đó để cung cấp context, không tự sắp theo UUID, không tự thêm nội dung bị thiếu. Không chứng nhận phép nối chuỗi sẽ khôi phục đúng full template: tiêu đề/context có thể lặp, một số mẫu có bản lặp ở nguồn khác.

Có 18 nhóm form chunks trùng `content_hash`; chúng có chunk/provision/source identities khác nhau, không phải duplicate `chunk_id`. Export không deduplicate hoặc trộn versions/sources. Cả hai JSONL không có duplicate `chunk_id`.

## Chất lượng và giới hạn sử dụng

**STRUCTURAL_FIDELITY_LIMITATION**: bảng DOCX đã được flatten thành plain text, thường phân cột bằng `|`. JSONL không lưu đủ merges, widths, styles, borders, pagination, vị trí chữ ký hay layout để tái tạo DOCX chính xác. Kiểm tra OOXML read-only trên ba source DOCX liên quan form fragments xác nhận có bảng, ô gộp ngang/dọc nhưng chunk chỉ có text. Số bảng/hàng trong audit là tổng của source DOCX được lấy mẫu, không phải số bảng của riêng chunk; đây không phải phép so toàn văn DOCX với chunk. Đối với tạo văn bản cần bố cục chính xác, dùng DOCX gốc đã bàn giao.

Mọi content hash đã khớp; provenance không bị mất, tất cả source IDs ánh xạ được về registry published. Cả 101 referenced raw files đều tồn tại và khớp SHA256. Không có missing `valid_from`, structural path hoặc empty source locator trong hai nhóm. Cả 343 chunks có `valid_to=null`; null không chứng minh còn hiệu lực vô hạn.

Metadata pháp lý có vấn đề cần review riêng: 119 form chunks có `valid_from=2020-01-01`; 59 form chunks có năm `issued_date` khác năm trong số hiệu văn bản (ví dụ NĐ 104/2022 và TT 11/2022 ghi `2020-01-01`). Audit liệt kê IDs, không sửa ngày. Tất cả 101 source records liên quan mang `verification_status=pending`, trong khi 343 chunks mang `verified`; exporter giữ nguyên hai cấp metadata này. Không suy “verified chunk” đồng nghĩa verified nguồn, current applicability hoặc đóng closeout.

Snapshot retrieval đủ để bàn giao text và provenance theo yêu cầu lọc; không được coi là template DOCX chuẩn để render tự động hoặc làm căn cứ xác nhận văn bản còn hiệu lực. Trước khi phát hành văn bản thực tế cần kiểm tra văn bản sửa đổi/thay thế, ngày áp dụng, đối tượng và template nguồn. Nếu cần sửa table fidelity, fragment offsets hoặc legal metadata, mở task riêng có owner duyệt; không rebuild ingestion trong task này.

## Tái lập và kiểm tra offline

Worktree thực thi riêng:
`C:/Users/Admin/.codex/visualizations/2026/10/16/01a1443e-cb2f-7541-ad6a-3c963e92a92d/legal-form-export`.

Source repository: `C:/Users/Admin/Project/AI_Agent_Luật_Lao_Động`.
Branch chuẩn bị: `codex/phase1-legal-form-export`, base export: `fac00ca23ee5395bae718be002363a02ad9c8389` (`main` khi bắt đầu). Owner đã yêu cầu đưa riêng gói export và tooling vào commit trên `main`, rồi push GitHub; owner xác nhận push cả 8 commits có sẵn phía trước GitHub main. Source commit trong manifest là thời điểm tạo dataset, không phải commit bàn giao sau đó.
Remote: `https://github.com/ghism137/AI_Agent_H-Tr-Tra-C-u-Lu-t-Lao-ng.git`.
Git common directory: `C:/Users/Admin/Project/AI_Agent_Luật_Lao_Động/.git`.

Main có dirty changes từ trước (28 tracked changes và nhiều untracked files), không stash/reset/checkout/rebase. Worktree sparse riêng ban đầu clean, chỉ checkout scripts/tests và root instructions, không checkout corpus. Managed-worktree creation qua app gặp Windows filename-too-long; dùng Git sparse worktree thủ công, không phải managed worktree của app. Không tái sử dụng worktree PD4-B/product-dev. Source data ignored được đọc trực tiếp bằng đường dẫn và pin hashes; không mặc định commit bao gồm data bytes.

Từ worktree riêng, dùng PowerShell:

```powershell
python -X utf8 scripts/export_legal_forms.py --source-repo 'C:/Users/Admin/Project/AI_Agent_Luật_Lao_Động' --export-timestamp '2026-10-16T17:30:15+07:00' --source-commit fac00ca23ee5395bae718be002363a02ad9c8389 --exporter-base-commit fac00ca23ee5395bae718be002363a02ad9c8389
$env:LEGAL_FORM_SOURCE_REPO = 'C:/Users/Admin/Project/AI_Agent_Luật_Lao_Động'
python -X utf8 -m unittest discover -s tests -p test_legal_form_export.py -v
```

Python 3.10+ stdlib; thực chạy Python 3.14. Timestamp và hai commit nguồn/base được pin để lặp lại cùng bytes sau khi HEAD thay đổi do commit bàn giao. Exporter từ chối active manifest/chunk/snapshot hash sai, duplicate IDs, missing provenance, output dưới source data/Git metadata, hoặc ghi đè output khác bytes. Destination trống có thể chọn bằng `--output-dir`; cùng inputs/timestamp/code/base commit thì JSONL/registry/audit/manifest tái lập giống từng byte. README, catalog và Git attributes là handoff docs, không do exporter sinh.

Focused test result: **17/17 PASS**, exit 0. Bao gồm parse/count/type/IDs, so nguyên bytes và toàn bộ fields, content hashes, legal metadata không đổi, registry mapping, table/fragment evidence, phân loại annex, hai replays deterministic, idempotence, protected sources không đổi và các negative checks. Lượt đầu có 4 lỗi quyền ghi temp mặc định của sandbox; test temp đã chuyển vào `.cache/legal-form-export-tests` trong worktree rồi chạy đủ bộ PASS. Không bỏ qua test hoặc thay acceptance để né lỗi.

Changed scope của commit export: thêm exporter, test module và folder `exports/legal_forms/v1`; không đưa dirty changes có sẵn vào commit. Không sửa source chunks, published manifest, active pointer, raw corpus hoặc ingestion logic. Không chạy crawl, API ngoài, ingestion, embedding/index hay full eval. Commit/push `main` theo chỉ dẫn mới của owner; không coi thao tác Git là publish lại Phase 1 release. Đây là builder delivery của task export; không có independent reviewer sign-off mới. Actual executor family GPT-6; exact runtime model ID/effort/token usage không được tool cung cấp nên ghi unavailable.

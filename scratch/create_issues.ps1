$gh = "C:\Program Files\GitHub CLI\gh.exe"

& $gh issue create --title "[P1-01] Lỗi hiệu lực giả (Stub Applicability) trong Corpus" --body "Có 13 stub đang được gán là ``verified`` với hash nguồn là ``unknown``. Gate 3 đang cho lọt các placeholder này thay vì chặn lại.`n`nYêu cầu xử lý: Cần loại bỏ hiệu lực giả khỏi corpus, đảm bảo mỗi relation phải có hash nguồn thật và được review cẩn thận." --label "bug"

& $gh issue create --title "[P1-02] Thiếu bằng chứng cho các chuỗi sửa đổi, bãi bỏ, hồi tố" --body "Legal review báo lỗi sai nghĩa ở các Nghị định 188/2025, 75/2023, 74/2025. Cần kiểm chứng lại vì các thay đổi chưa có bằng chứng đầy đủ." --label "bug"

& $gh issue create --title "[P1-03] Fidelity review toàn văn bản chưa hoàn tất" --body "Vẫn còn 46 document và 30 sample đang chờ review (pending). Dữ liệu Candidate đã tăng vọt lên hơn 20.000 chunks nên review cũ không còn giá trị." --label "bug"

& $gh issue create --title "[P1-04] Rủi ro Materialization ghi đè sai thời gian hiệu lực" --body "Quá trình này đang sửa trực tiếp ``valid_from``/``valid_to`` trên version, có nguy cơ xóa lịch sử hoặc làm sai hiệu lực khi các operation giao nhau." --label "bug"

& $gh issue create --title "[P1-05] Acceptance Gate chưa kiểm tra đủ bằng chứng" --body "Gate 2 và Gate 3 đánh PASS kể cả khi dữ kiện là ``unknown``. Checklist báo ``yes`` nhưng chi tiết vẫn đang ``pending``." --label "bug"

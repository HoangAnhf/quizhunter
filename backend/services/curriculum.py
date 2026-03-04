"""Chương trình SGK Việt Nam — hướng dẫn AI tạo câu hỏi đúng lớp."""

# Mapping: (môn, lớp) → danh sách chủ đề chính
CURRICULUM = {
    ("Toán học", 1): "Các số đến 100, phép cộng trừ trong phạm vi 100, hình vuông hình tròn hình tam giác, đo độ dài cm",
    ("Toán học", 2): "Các số đến 1000, phép cộng trừ có nhớ, phép nhân chia trong bảng, đo dài m km, đo khối lượng kg",
    ("Toán học", 3): "Các số đến 100000, nhân chia số có nhiều chữ số, chu vi diện tích hình chữ nhật hình vuông, thống kê đơn giản",
    ("Toán học", 4): "Phân số, các phép tính với phân số, số thập phân, góc nhọn góc tù góc bẹt, hình bình hành hình thoi, trung bình cộng, biểu đồ",
    ("Toán học", 5): "Số thập phân nâng cao, tỉ số phần trăm, hình tròn chu vi diện tích, hình hộp chữ nhật hình lập phương thể tích, tốc độ quãng đường thời gian",
    ("Toán học", 6): "Số tự nhiên, tính chia hết, số nguyên tố ước bội ƯCLN BCNN, số nguyên, phân số, số thập phân, góc, đường thẳng, tia, đoạn thẳng",
    ("Toán học", 7): "Số hữu tỉ, số thực, căn bậc hai, tỉ lệ thức, đại lượng tỉ lệ thuận tỉ lệ nghịch, thống kê, tam giác bằng nhau, tam giác cân đều vuông, quan hệ giữa các yếu tố trong tam giác",
    ("Toán học", 8): "Phân thức đại số, phương trình bậc nhất một ẩn, bất phương trình bậc nhất, tứ giác (hình thang hình bình hành hình chữ nhật hình thoi hình vuông), diện tích đa giác, hình lăng trụ hình chóp, định lý Talet, tam giác đồng dạng",
    ("Toán học", 9): "Căn bậc hai căn bậc ba, hàm số bậc nhất y=ax+b, hệ phương trình bậc nhất hai ẩn, phương trình bậc hai ax²+bx+c=0, hệ thức lượng trong tam giác vuông (sin cos tan), đường tròn (tiếp tuyến dây cung góc nội tiếp), hình trụ hình nón hình cầu",
    ("Toán học", 10): "Mệnh đề tập hợp, hàm số bậc hai, phương trình quy về bậc hai, bất phương trình bậc hai, hệ bất phương trình, thống kê, vectơ, tích vô hướng, tọa độ trong mặt phẳng, phương trình đường thẳng đường tròn, lượng giác (sin cos tan cot), công thức lượng giác",
    ("Toán học", 11): "Hàm số lượng giác, phương trình lượng giác, tổ hợp hoán vị chỉnh hợp, xác suất, nhị thức Newton, dãy số cấp số cộng cấp số nhân, giới hạn dãy số hàm số, đạo hàm, phép dời hình phép đồng dạng, đường thẳng mặt phẳng trong không gian, quan hệ song song vuông góc",
    ("Toán học", 12): "Ứng dụng đạo hàm khảo sát hàm số, cực trị GTLN GTNN, tiệm cận, hàm số mũ logarit, tích phân nguyên hàm, số phức, thể tích khối đa diện khối tròn xoay, phương trình mặt phẳng đường thẳng trong Oxyz, khoảng cách góc trong không gian",

    ("Vật lý", 6): "Đo lường (đo độ dài khối lượng thể tích thời gian), lực cân bằng lực, máy cơ đơn giản (đòn bẩy ròng rọc mặt phẳng nghiêng)",
    ("Vật lý", 7): "Quang học (gương phẳng gương cầu, sự phản xạ ánh sáng), âm học, điện học cơ bản (dòng điện mạch điện, cường độ hiệu điện thế)",
    ("Vật lý", 8): "Cơ học (chuyển động vận tốc, lực ma sát áp suất, lực đẩy Acsimet, công cơ học, công suất, cơ năng), nhiệt học (dẫn nhiệt đối lưu bức xạ, nhiệt lượng, phương trình cân bằng nhiệt, sự nóng chảy bay hơi)",
    ("Vật lý", 9): "Điện học (định luật Ohm, điện trở, đoạn mạch nối tiếp song song, công suất điện, điện năng), điện từ học (nam châm từ trường, lực từ cảm ứng điện từ), quang học (thấu kính hội tụ phân kì, mắt kính lúp), năng lượng hạt nhân",
    ("Vật lý", 10): "Động học (chuyển động thẳng đều biến đổi đều, rơi tự do, chuyển động tròn đều), động lực học (ba định luật Newton, lực ma sát lực hướng tâm), tĩnh học (quy tắc hợp lực momen), các định luật bảo toàn (động lượng năng lượng), chất khí (phương trình trạng thái khí lí tưởng)",
    ("Vật lý", 11): "Điện tích điện trường, tụ điện, dòng điện không đổi (định luật Ohm mạch kín, ghép nguồn), dòng điện trong các môi trường, từ trường (lực Lorentz, cảm ứng điện từ, tự cảm), khúc xạ ánh sáng, lăng kính, thấu kính, mắt và dụng cụ quang",
    ("Vật lý", 12): "Dao động cơ (con lắc lò xo đơn, dao động tắt dần cưỡng bức cộng hưởng), sóng cơ (giao thoa sóng dừng), sóng âm, dòng điện xoay chiều (máy phát điện máy biến áp), sóng điện từ, sóng ánh sáng (giao thoa tán sắc), lượng tử ánh sáng (quang điện), vật lý hạt nhân (phóng xạ phản ứng hạt nhân)",

    ("Hóa học", 8): "Chất nguyên tử phân tử, nguyên tố hóa học bảng tuần hoàn, phản ứng hóa học, mol tỉ khối, dung dịch nồng độ, oxi không khí, hidro nước, axit bazơ muối",
    ("Hóa học", 9): "Kim loại (tính chất dãy hoạt động, nhôm sắt), phi kim (clo cacbon silic), bảng tuần hoàn nâng cao, hiđrocacbon (metan etilen axetilen benzen), rượu etylic axit axetic chất béo, glucozơ saccarozơ tinh bột xenlulozơ, protein polime",
    ("Hóa học", 10): "Nguyên tử (thành phần cấu tạo, lớp electron), bảng tuần hoàn và định luật tuần hoàn, liên kết hóa học (ion cộng hóa trị), phản ứng oxi hóa khử, nhóm halogen (F Cl Br I), oxi lưu huỳnh, tốc độ phản ứng cân bằng hóa học",
    ("Hóa học", 11): "Sự điện li (axit bazơ muối, pH), nitơ photpho (NH3 HNO3 phân bón), cacbon silic (CO CO2 SiO2), đại cương hóa hữu cơ, hiđrocacbon no không no thơm, ancol phenol anđehit axit cacboxylic este",
    ("Hóa học", 12): "Este lipit xà phòng, cacbohiđrat (glucozơ saccarozơ tinh bột xenlulozơ), amin amino axit protein, polime vật liệu polime, đại cương kim loại (dãy điện hóa điện phân), kim loại kiềm kiềm thổ nhôm, sắt crom, nhận biết chất, hóa học và đời sống",

    ("Sinh học", 6): "Tế bào thực vật, rễ thân lá hoa quả hạt, các nhóm thực vật (tảo rêu dương xỉ hạt trần hạt kín), vai trò thực vật",
    ("Sinh học", 7): "Động vật không xương sống (trùng giun thân mềm chân khớp), động vật có xương sống (cá lưỡng cư bò sát chim thú), tiến hóa động vật, đa dạng sinh học",
    ("Sinh học", 8): "Cơ thể người: xương cơ, tuần hoàn (tim mạch máu), hô hấp, tiêu hóa, bài tiết, da, thần kinh, giác quan, nội tiết, sinh sản",
    ("Sinh học", 9): "Di truyền (Mendel, NST, ADN, gen, đột biến, di truyền người), sinh vật và môi trường (quần thể quần xã hệ sinh thái), con người và môi trường, bảo vệ môi trường",
    ("Sinh học", 10): "Thành phần hóa học tế bào (nước cacbohidrat lipit protein axit nucleic), cấu trúc tế bào (nhân ti thể lưới nội chất), chuyển hóa vật chất năng lượng (enzim hô hấp quang hợp), phân bào (nguyên phân giảm phân), vi sinh vật",
    ("Sinh học", 11): "Chuyển hóa vật chất ở thực vật (trao đổi nước khoáng quang hợp hô hấp), sinh trưởng phát triển thực vật (phitohomon), sinh sản thực vật, chuyển hóa ở động vật (tiêu hóa hô hấp tuần hoàn), cảm ứng ở động vật, sinh trưởng sinh sản động vật",
    ("Sinh học", 12): "Di truyền phân tử (gen mã di truyền phiên mã dịch mã đột biến gen), di truyền NST (quy luật Mendel liên kết gen hoán vị gen), di truyền quần thể, tiến hóa (Darwin học thuyết tiến hóa tổng hợp), sinh thái học (quần thể quần xã hệ sinh thái sinh quyển)",

    ("Lịch sử", 6): "Lịch sử thế giới cổ đại: xã hội nguyên thủy, Ai Cập Lưỡng Hà Ấn Độ Trung Quốc cổ đại, Hy Lạp La Mã cổ đại, Đông Nam Á cổ đại",
    ("Lịch sử", 7): "Lịch sử thế giới trung đại: phong kiến châu Âu, Trung Quốc Ấn Độ phong kiến, các cuộc phát kiến địa lý. Việt Nam: Ngô Đinh Lê Lý Trần Hồ, kháng chiến chống Tống Nguyên Mông",
    ("Lịch sử", 8): "Cách mạng tư sản (Anh Pháp Mỹ), cách mạng công nghiệp, chủ nghĩa tư bản, phong trào công nhân Marx, Chiến tranh thế giới I. Việt Nam: thực dân Pháp xâm lược, phong trào chống Pháp, Phan Bội Châu Phan Châu Trinh",
    ("Lịch sử", 9): "Chiến tranh thế giới II, trật tự hai cực Yalta, phong trào giải phóng dân tộc. Việt Nam: Đảng CSVN ra đời, Cách mạng tháng Tám, kháng chiến chống Pháp (Điện Biên Phủ), kháng chiến chống Mỹ, thống nhất đất nước",
    ("Lịch sử", 10): "Xã hội nguyên thủy, các nền văn minh cổ đại phương Đông phương Tây, xã hội phong kiến, Việt Nam thời nguyên thủy đến thế kỉ X",
    ("Lịch sử", 11): "Cách mạng tư sản, chiến tranh thế giới I II, cách mạng tháng Mười Nga, phong trào giải phóng dân tộc. Việt Nam: phong trào yêu nước đầu TK XX, Nguyễn Ái Quốc, thành lập Đảng",
    ("Lịch sử", 12): "Trật tự thế giới sau 1945, chiến tranh lạnh, Liên Xô Đông Âu, các nước Á Phi Mỹ Latinh. Việt Nam: CMT8, kháng chiến chống Pháp (chiến dịch Điện Biên Phủ Hiệp định Genève), kháng chiến chống Mỹ (Tết Mậu Thân chiến dịch HCM), xây dựng CNXH đổi mới",

    ("Ngữ văn", 6): "Truyện dân gian (truyền thuyết cổ tích ngụ ngôn), thơ lục bát, văn tự sự miêu tả, tiếng Việt cơ bản (từ loại câu đơn)",
    ("Ngữ văn", 7): "Ca dao tục ngữ, thơ trung đại (Hồ Xuân Hương Bà Huyện Thanh Quan Nguyễn Trãi), văn nghị luận chứng minh giải thích, văn biểu cảm",
    ("Ngữ văn", 8): "Truyện kí Việt Nam (Lão Hạc Tắt đèn Tôi đi học), thơ mới (Nhớ rừng Ông đồ Quê hương), văn nghị luận, câu phủ định câu cảm thán, hội thoại",
    ("Ngữ văn", 9): "Truyện Kiều (Nguyễn Du), Chuyện người con gái Nam Xương, thơ hiện đại (Đồng chí Bài thơ về tiểu đội xe không kính Viếng lăng Bác Mùa xuân nho nhỏ), truyện hiện đại (Làng Lặng lẽ Sa Pa Chiếc lược ngà), văn nghị luận xã hội văn học",
    ("Ngữ văn", 10): "Văn học dân gian (sử thi Đăm Săn, truyện cổ, ca dao), văn học trung đại (Nguyễn Trãi Nguyễn Du Hồ Xuân Hương), nghị luận văn học, làm văn nghị luận",
    ("Ngữ văn", 11): "Văn học hiện đại: Xuân Diệu Huy Cận Hàn Mặc Tử, Nam Cao (Chí Phèo), Vũ Trọng Phụng (Số đỏ), thơ mới, nghị luận xã hội văn học nâng cao",
    ("Ngữ văn", 12): "Tuyên ngôn độc lập (HCM), Tây Tiến (Quang Dũng), Việt Bắc (Tố Hữu), Đất nước (Nguyễn Khoa Điềm), Sóng (Xuân Quỳnh), Vợ chồng A Phủ (Tô Hoài), Vợ nhặt (Kim Lân), Rừng xà nu (Nguyễn Trung Thành), Chiếc thuyền ngoài xa (Nguyễn Minh Châu), nghị luận văn học",

    ("Tiếng Anh", 6): "Greetings, school things, daily routines, family members, seasons weather, sports hobbies, places in town, present simple tense, there is/are",
    ("Tiếng Anh", 7): "Hobbies, health, community service, music, food, festivals, traffic, present perfect tense, comparisons, should/must",
    ("Tiếng Anh", 8): "Leisure activities, life in the countryside/city, peoples of Vietnam, festivals, pollution, English speaking countries, past simple continuous, passive voice, reported speech",
    ("Tiếng Anh", 9): "Local environment, city life, teen stress, life in the past, wonders of Vietnam, conditional sentences, relative clauses, wish sentences, phrasal verbs",
    ("Tiếng Anh", 10): "Family life, music, community, gender equality, inventions, national parks, present perfect vs past simple, gerund infinitive, reported speech, passive voice",
    ("Tiếng Anh", 11): "Generation gap, relationships, becoming independent, caring for those in need, ASEAN, global warming, further education, future tenses, modal verbs, cleft sentences",
    ("Tiếng Anh", 12): "Life stories, urbanization, green living, artificial intelligence, cultural identity, endangered species, career choices, advanced grammar review, writing essays",

    ("Địa lý", 6): "Trái Đất trong hệ Mặt Trời, bản đồ tỉ lệ, kinh tuyến vĩ tuyến, các đới khí hậu, địa hình (núi đồng bằng cao nguyên), sông ngòi biển đại dương",
    ("Địa lý", 7): "Dân cư thế giới, các môi trường địa lý (nhiệt đới ôn đới hàn đới hoang mạc), đặc điểm kinh tế xã hội châu Phi châu Mỹ châu Âu châu Á châu Đại Dương",
    ("Địa lý", 8): "Tự nhiên Việt Nam: vị trí địa hình khí hậu sông ngòi đất đai sinh vật biển đảo, các miền tự nhiên Bắc Trung Nam",
    ("Địa lý", 9): "Dân cư Việt Nam, kinh tế Việt Nam (nông nghiệp công nghiệp dịch vụ), các vùng kinh tế (Đồng bằng sông Hồng, Trung du miền núi phía Bắc, Bắc Trung Bộ, Duyên hải Nam Trung Bộ, Tây Nguyên, Đông Nam Bộ, Đồng bằng sông Cửu Long)",
    ("Địa lý", 10): "Bản đồ, vũ trụ Trái Đất, khí quyển thủy quyển thạch quyển sinh quyển, địa lý dân cư, cơ cấu nền kinh tế thế giới, địa lý nông nghiệp công nghiệp dịch vụ, môi trường phát triển bền vững",
    ("Địa lý", 11): "Khu vực Đông Nam Á, Mỹ, Liên bang Nga, Nhật Bản, Trung Quốc, EU, Úc — tự nhiên dân cư kinh tế",
    ("Địa lý", 12): "Việt Nam: vị trí tự nhiên, đặc điểm dân cư lao động, chuyển dịch cơ cấu kinh tế, địa lý ngành (nông lâm thủy sản, công nghiệp, dịch vụ du lịch), địa lý các vùng kinh tế, biển đảo Việt Nam",

    ("Tin học", 6): "Thông tin dữ liệu, máy tính và thiết bị số, hệ điều hành, phần mềm soạn thảo văn bản, Internet an toàn",
    ("Tin học", 7): "Xử lý thông tin, phần mềm trình chiếu, bảng tính điện tử cơ bản, mạng máy tính Internet, đạo đức pháp luật CNTT",
    ("Tin học", 8): "Lập trình cơ bản (biến kiểu dữ liệu, câu lệnh điều kiện vòng lặp), phần mềm đồ họa, bảng tính nâng cao, an toàn thông tin",
    ("Tin học", 9): "Lập trình nâng cao (mảng hàm thủ tục), cơ sở dữ liệu (khái niệm tạo bảng truy vấn), mạng máy tính, dự án CNTT",
    ("Tin học", 10): "Đại cương CNTT, hệ điều hành, soạn thảo văn bản nâng cao, bảng tính nâng cao, Internet và truyền thông, cơ sở dữ liệu quan hệ",
    ("Tin học", 11): "Lập trình Pascal/Python (kiểu dữ liệu biến hằng, cấu trúc rẽ nhánh lặp, kiểu mảng xâu, chương trình con, tệp), thuật toán sắp xếp tìm kiếm",
    ("Tin học", 12): "Cơ sở dữ liệu quan hệ, hệ quản trị CSDL (Access), SQL cơ bản (SELECT INSERT UPDATE DELETE), thiết kế CSDL, bảo mật CSDL",

    ("GDCD", 6): "Tự nhận thức bản thân, yêu thương gia đình, tôn trọng sự khác biệt, tiết kiệm, ứng xử với bạn bè, an toàn giao thông",
    ("GDCD", 7): "Tự tin, sống giản dị, trung thực, bảo vệ môi trường, quyền trẻ em, quyền được bảo vệ chăm sóc giáo dục",
    ("GDCD", 8): "Tôn trọng lẽ phải, liêm khiết, pháp luật và kỷ luật, quyền và nghĩa vụ công dân, phòng chống tệ nạn xã hội, quyền khiếu nại tố cáo",
    ("GDCD", 9): "Chí công vô tư, dân chủ kỷ luật, bảo vệ hòa bình, hợp tác và phát triển, quyền nghĩa vụ lao động, quyền tự do kinh doanh, nghĩa vụ bảo vệ Tổ quốc",
    ("GDCD", 10): "Thế giới quan duy vật, phương pháp luận biện chứng, tồn tại xã hội ý thức xã hội, con người và sự phát triển xã hội",
    ("GDCD", 11): "Kinh tế chính trị: sản xuất của cải vật chất, hàng hóa tiền tệ thị trường, quy luật giá trị cung cầu cạnh tranh, công nghiệp hóa hiện đại hóa, kinh tế nhiều thành phần",
    ("GDCD", 12): "Pháp luật và đời sống, quyền bình đẳng (giới hôn nhân gia đình lao động kinh doanh), quyền tự do cơ bản của công dân (tự do ngôn luận tín ngưỡng bất khả xâm phạm thân thể nhà ở), pháp luật với sự phát triển bền vững",

    ("Công nghệ", 6): "Vật liệu trong gia đình, an toàn thực phẩm, may mặc, nhà ở, nấu ăn",
    ("Công nghệ", 7): "Trồng trọt (đất phân bón giống cây trồng), chăn nuôi (giống thức ăn vệ sinh), lâm nghiệp thủy sản",
    ("Công nghệ", 8): "Vẽ kỹ thuật, cơ khí (vật liệu dụng cụ gia công), chi tiết máy và lắp ghép, truyền chuyển động",
    ("Công nghệ", 9): "Kỹ thuật điện (mạch điện, đo lường điện, an toàn điện), lắp đặt mạng điện trong nhà",
    ("Công nghệ", 10): "Vẽ kỹ thuật nâng cao, cơ khí chế tạo, động cơ đốt trong, ô tô xe máy",
    ("Công nghệ", 11): "Kỹ thuật điện tử (linh kiện điện tử, mạch điện tử), kỹ thuật số, vi xử lý",
    ("Công nghệ", 12): "Kỹ thuật điện (máy điện máy biến áp động cơ điện), mạng điện sản xuất, an toàn điện công nghiệp",

    ("Thể dục", 6): "Đội hình đội ngũ, bài tập thể dục phát triển chung, chạy ngắn chạy bền, nhảy xa nhảy cao, bóng đá bóng chuyền bóng rổ",
    ("Thể dục", 7): "Chạy ngắn 60m 80m, chạy bền, nhảy xa kiểu ngồi, ném bóng, bóng chuyền bóng đá bóng rổ",
    ("Thể dục", 8): "Chạy ngắn 100m, nhảy xa kiểu ưỡn thân, đá cầu, bóng chuyền bóng đá, thể dục nhịp điệu",
    ("Thể dục", 9): "Chạy ngắn 100m nâng cao, chạy bền 1000m, nhảy xa nhảy cao, bóng chuyền bóng đá bóng rổ, thể dục tự chọn",
    ("Thể dục", 10): "Chạy cự li ngắn trung bình, nhảy xa nhảy cao, ném đẩy, thể dục dụng cụ, bóng chuyền bóng đá bóng rổ, cầu lông",
    ("Thể dục", 11): "Chạy tiếp sức, nhảy xa nhảy cao nâng cao, thể dục nhịp điệu, bóng chuyền bóng đá bóng rổ, cầu lông",
    ("Thể dục", 12): "Chạy bền nâng cao, nhảy xa nhảy cao hoàn thiện, bóng chuyền bóng đá bóng rổ nâng cao, cầu lông bóng bàn, thể dục tự chọn",
}


def get_curriculum_hint(subject: str, grade: int) -> str:
    """Lấy mô tả chương trình SGK cho môn + lớp."""
    return CURRICULUM.get((subject, grade), "")

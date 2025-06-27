from bot.modules import enhanced_behavior

def test_detect_conversation_type():
    assert enhanced_behavior.detect_conversation_type("Це був баг у коді") == "технічне"
    assert enhanced_behavior.detect_conversation_type("Який сенс життя?") == "філософське"
    assert enhanced_behavior.detect_conversation_type("хаха, це мем!") == "веселе"
    assert enhanced_behavior.detect_conversation_type("дурак, не згоден") == "конфлікт"
    assert enhanced_behavior.detect_conversation_type("погода сьогодні гарна") == "побутове"

def test_detect_mood():
    assert enhanced_behavior.detect_mood("дякую, все класно!") == "позитив"
    assert enhanced_behavior.detect_mood("сумно і болить") == "негатив"
    assert enhanced_behavior.detect_mood("можливо, цікаво") == "нейтрал"

def test_calculate_engagement_level():
    assert enhanced_behavior.calculate_engagement_level("гряг, допоможи!", "технічне", "позитив") >= 7
    assert enhanced_behavior.calculate_engagement_level("", "побутове", "нейтрал") >= 1

def test_should_bot_respond():
    assert enhanced_behavior.should_bot_respond("гряг, привіт!", "технічне", "позитив", 8) is True
    assert isinstance(enhanced_behavior.should_bot_respond("", "побутове", "нейтрал", 2), bool)

def test_get_response_tone():
    assert enhanced_behavior.get_response_tone("технічне", "позитив") == "розумний_жарт"
    assert enhanced_behavior.get_response_tone("побутове", "нейтрал") == "легкий_гумор"

import unittest

from scripts.build_ielts_plagiarism_corpus import (
    SOURCES,
    prepare_rows,
    sample_diverse,
    text_hash,
)


def task2(text, question="Some people prefer online education. Discuss both views.", topic="Education"):
    return dict(essay_id="example", question=question, essay_text=text, topic=topic)


class PlagiarismCorpusTests(unittest.TestCase):
    def test_dedup_and_exclusion_preserve_the_original_text(self):
        original = "  This are my argument.\n\nI has two reason.  "
        rows = [
            task2(original),
            task2("THIS ARE MY ARGUMENT. I HAS TWO REASON."),
            task2("This essay is reserved for benchmark evaluation."),
        ]
        selected, counts = prepare_rows(rows, SOURCES[1], {text_hash(rows[2]["essay_text"])}, set(), min_words=3)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["text"], original)
        self.assertEqual(counts["duplicate"], 1)
        self.assertEqual(counts["evaluation_overlap"], 1)
        self.assertEqual(set(selected[0]), {"source_id", "text", "task_type", "exam_question", "topic", "source_url"})

    def test_letters_short_text_and_task1_reports_do_not_become_task2(self):
        rows = [
            task2("Dear Sir, I am writing to ask for your support."),
            task2("This is a short letter to the city mayor.", "Write a letter to the mayor."),
            task2(
                "The graph illustrates the number of visitors to a museum.",
                "The graph below shows the number of visitors. Summarise the information.",
            ),
            task2("Too short"),
            task2(None),
        ]
        selected, counts = prepare_rows(rows, SOURCES[1], set(), set(), min_words=4)
        self.assertEqual(selected, [])
        self.assertEqual(sum(counts.values()), len(rows))

    def test_task1_requires_academic_visual_prompt(self):
        rows = [
            dict(topic="Bar Chart", subject="The chart below shows school transport.", content="This are a report."),
            dict(topic="Bar Chart", subject="Write a letter to your friend.", content="Dear Tom, How are you?"),
            dict(topic="Unknown", subject="Discuss both views.", content="This is an essay."),
        ]
        selected, _ = prepare_rows(rows, SOURCES[0], set(), set(), min_words=3)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["task_type"], "task1")
        self.assertNotIn("license", selected[0])

    def test_sampling_is_repeatable_and_covers_topics_and_prompts(self):
        rows = [
            dict(source_id=str(i), topic=topic, exam_question=question)
            for topic, question, indices in [
                ("A", "q1", range(20)),
                ("A", "q2", range(20, 30)),
                ("B", "q3", range(30, 32)),
            ]
            for i in indices
        ]
        sample = sample_diverse(rows, 4)
        self.assertEqual(sample, sample_diverse(list(reversed(rows)), 4))
        self.assertEqual({r["exam_question"] for r in sample}, {"q1", "q2", "q3"})
        self.assertEqual(len(sample), 4)
        with self.assertRaises(ValueError):
            sample_diverse(rows, 100)

    def test_many_unique_questions_do_not_crowd_out_other_topics(self):
        rows = [dict(source_id=str(i), topic="A", exam_question=f"q{i}") for i in range(30)]
        rows += [dict(source_id=t, topic=t, exam_question="other") for t in ("B", "C", "D")]
        self.assertEqual({r["topic"] for r in sample_diverse(rows, 4)}, {"A", "B", "C", "D"})


if __name__ == "__main__":
    unittest.main()

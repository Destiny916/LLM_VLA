import tempfile
import unittest
from pathlib import Path

from llm_vla.rag import load_rag_documents, retrieve_context


class RagTests(unittest.TestCase):
    def test_load_rag_documents_splits_markdown_by_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "actions.md"
            doc.write_text(
                "# 动作目录\n\n"
                "总说明。\n\n"
                "## lift_up\n\n"
                "机械臂上举，arm_lift 变为 up。\n\n"
                "## put_down\n\n"
                "机械臂放下，arm_lift 变为 down。\n",
                encoding="utf-8",
            )

            documents = load_rag_documents(root)

        titles = [document.title for document in documents]
        self.assertEqual(["动作目录", "lift_up", "put_down"], titles)
        self.assertTrue(all(document.path == "actions.md" for document in documents))
        self.assertIn("机械臂上举", documents[1].content)
        self.assertIn("机械臂放下", documents[2].content)

    def test_retrieve_context_ranks_chinese_and_token_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "action_catalog.md").write_text(
                "# 动作知识库\n\n"
                "## lift_up\n\n"
                "机械臂上举，后续左转保持上举状态。\n\n"
                "## put_down\n\n"
                "机械臂放下，put_down 不是 reset。\n",
                encoding="utf-8",
            )
            (root / "task_rules.md").write_text(
                "# 任务规则\n\n"
                "## 任务级复位\n\n"
                "每个任务完成后必须 reset，然后 hold_reset。\n",
                encoding="utf-8",
            )
            documents = load_rag_documents(root)

            hits = retrieve_context("机械臂上举后左转", documents, top_k=2)

        self.assertEqual(2, len(hits))
        self.assertEqual("lift_up", hits[0].title)
        self.assertEqual("action_catalog.md", hits[0].path)
        self.assertGreater(hits[0].score, hits[1].score)
        self.assertIn("机械臂上举", hits[0].snippet)

    def test_retrieve_context_returns_empty_for_no_terms(self):
        documents = load_rag_documents(Path(__file__).resolve().parents[1] / "harness" / "rag")

        hits = retrieve_context("   ", documents)

        self.assertEqual([], hits)

    def test_project_rag_documents_are_searchable(self):
        rag_root = Path(__file__).resolve().parents[1] / "harness" / "rag"

        documents = load_rag_documents(rag_root)
        hits = retrieve_context("放下动作 put_down 任务级复位", documents, top_k=8)

        self.assertGreaterEqual(len(documents), 7)
        self.assertTrue(any(hit.title == "put_down" for hit in hits), [(hit.title, hit.path, hit.score) for hit in hits])
        self.assertTrue(any("任务级复位" in hit.content for hit in hits))

    def test_two_joint_policy_is_searchable(self):
        rag_root = Path(__file__).resolve().parents[1] / "harness" / "rag"

        documents = load_rag_documents(rag_root)
        hits = retrieve_context("两关节 panda_joint2 上下运动 锁定", documents, top_k=3)

        self.assertTrue(any(hit.title == "两关节控制策略" for hit in hits))


if __name__ == "__main__":
    unittest.main()

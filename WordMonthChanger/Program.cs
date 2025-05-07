using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace ConsoleApp1
{
    internal static class Program
    {
        private static void Main()
        {
            try
            {
                Console.WriteLine("=== Word 月份和年份替换工具 ===");

                // 获取用户输入
                var ( oldMonth, newMonth) = GetUserInputForMonth();
                Console.WriteLine($"将替换所有 {oldMonth}月 为 {newMonth}月\n");

                // 获取年份输入
                var (oldYear, newYear) = GetUserInputForYear();
                if (oldYear.HasValue && newYear.HasValue)
                {
                    Console.WriteLine($"将替换所有 {oldYear} 为 {newYear}\n");
                }

                // 获取文件列表
                var files = GetWordFiles(Directory.GetCurrentDirectory());
                if (files.Length == 0)
                {
                    Console.WriteLine("没有找到任何文件");
                    return;
                }
                Console.WriteLine($"找到 {files.Length} 个文件");

                // 处理文件
                ProcessFiles(files, oldMonth, newMonth, oldYear, newYear);

                Console.WriteLine("\n处理完成!");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n发生错误:{ex.Message}");
            }
            finally
            {
                Console.WriteLine("按任意键退出...");
                Console.ReadKey();
            }
        }

        static (int oldMonth, int newMonth) GetUserInputForMonth()
        {
            Console.Write("请输入要替换的月份数字(1-12): ");
            if (!int.TryParse(Console.ReadLine(), out int oldMonth) || oldMonth < 1 || oldMonth > 12)
                throw new ArgumentException("无效的月份数字");

            Console.Write("请输入新的月份数字(1-12): ");
            if (!int.TryParse(Console.ReadLine(), out int newMonth) || newMonth < 1 || newMonth > 12)
                throw new ArgumentException("无效的月份数字");

            if (oldMonth == newMonth)
                throw new ArgumentException("新旧月份不能相同");

            return (oldMonth, newMonth);
        }

            static (int? oldYear, int? newYear) GetUserInputForYear()
            {
                Console.Write("是否需要替换年份？(y/n): ");
                var response = Console.ReadLine()?.Trim().ToLower(); // 声明为可空字符串
                if (response == null || response != "y") // 检查是否为 null 或非 "y"
                {
                    return (null, null);
                }
            
                Console.Write("请输入要替换的年份: ");
                if (!int.TryParse(Console.ReadLine(), out int oldYear))
                    throw new ArgumentException("无效的年份");
            
                Console.Write("请输入新的年份: ");
                if (!int.TryParse(Console.ReadLine(), out int newYear))
                    throw new ArgumentException("无效的年份");
            
                if (oldYear == newYear)
                    throw new ArgumentException("新旧年份不能相同");
            
                return (oldYear, newYear);
            }

        static FileInfo[] GetWordFiles(string directory)
        {
            var dirInfo = new DirectoryInfo(directory);
            return dirInfo.GetFiles("*.doc?", SearchOption.AllDirectories) // 匹配 .docx 和 .docm
                         .Where(f => (f.Attributes & FileAttributes.Hidden) == 0)
                         .ToArray();
        }

        private static void ProcessFiles(FileInfo[] files, int oldMonth, int newMonth, int? oldYear, int? newYear)
        {
            var processed = 0;
            foreach (var file in files)
            {
                processed++;
                Console.Write($"\r处理进度: {processed}/{files.Length} 当前文件: {file.Name}");

                var tempPath = Path.Combine(
                    file.DirectoryName!,
                    Path.GetFileNameWithoutExtension(file.Name) + "_temp.docx");

                try
                {
                    var contentModified = ProcessFileContent(file.FullName, tempPath, oldMonth, newMonth, oldYear, newYear);

                    var newFileName = ProcessFileName(file.Name, oldMonth, newMonth, oldYear, newYear);

                    var newPath = Path.Combine(file.DirectoryName!, newFileName);

                    // 检查条件:如果内容被修改或者文件名不相同则更新文件名
                    if (contentModified || file.Name != newFileName)
                    {
                        if (File.Exists(file.FullName))
                        {
                            File.Delete(file.FullName);
                        }
                        File.Move(tempPath, newPath);
                        Console.WriteLine($"\n文件已更新: {file.Name} -> {newFileName}");
                    }
                    else
                    {
                        File.Delete(tempPath);
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"\n处理文件 {file.Name} 时发生错误: {ex.Message}");
                    if (File.Exists(tempPath)) File.Delete(tempPath);
                }  
            }
        }

        static bool ProcessFileContent(string sourcePath, string tempPath, int oldMonth, int newMonth, int? oldYear, int? newYear)
        {
            var modified = false;
            File.Copy(sourcePath, tempPath, true);

            using var doc = WordprocessingDocument.Open(tempPath, true);
            // 处理正文
            modified |= ReplaceContent(doc.MainDocumentPart, oldMonth, newMonth, oldYear, newYear);

            // 处理页眉
            foreach (var header in doc.MainDocumentPart.HeaderParts)
            {
                modified |= ReplaceContent(header, oldMonth, newMonth, oldYear, newYear);
            }

            // 处理页脚

            return doc.MainDocumentPart.FooterParts.Aggregate(modified, (current, footer) => current | ReplaceContent(footer, oldMonth, newMonth, oldYear, newYear));
        }

        // 使用 OpenXML SDK 替换文档内容
        private static bool ReplaceContent(OpenXmlPart part, int oldMonth, int newMonth, int? oldYear, int? newYear)
        {
            var modified = false;

            // 替换月份
            var monthSearch = $"{oldMonth}月";
            var monthReplace = $"{newMonth}月";

            // 替换年份（如果有）
            var yearSearch = oldYear?.ToString();
            var yearReplace = newYear?.ToString();

            foreach (var text in part.RootElement.Descendants<Text>())
            {
                // 合并分割的文本节点
                string originalText = text.Text;

                // 替换月份
                if (originalText.Contains(monthSearch))
                {
                    text.Text = originalText.Replace(monthSearch, monthReplace);
                    modified = true;
                }

                // 替换年份（仅当年份不为 null 时）
                if (yearSearch == null || yearReplace == null || !originalText.Contains(yearSearch)) continue;
                text.Text = originalText.Replace(yearSearch, yearReplace);
                modified = true;
            }

            return modified;
        }

        // 使用简单字符串替换实现文件名中月份更新
        private static string ProcessFileName(string fileName, int oldMonth, int newMonth, int? oldYear, int? newYear)
        {
            // 分离文件名和扩展名
            var nameWithoutExt = Path.GetFileNameWithoutExtension(fileName);
            var extension = Path.GetExtension(fileName);

            var monthTarget = oldMonth + "月";
            var monthReplacement = newMonth + "月";
            var newName = nameWithoutExt.Contains(monthTarget)
                                ? nameWithoutExt.Replace(monthTarget, monthReplacement)
                                : nameWithoutExt;

            if (!oldYear.HasValue || !newYear.HasValue) return newName + extension;
            var yearTarget = oldYear.Value.ToString();
            var yearReplacement = newYear.Value.ToString();
            newName = newName.Contains(yearTarget)
                ? newName.Replace(yearTarget, yearReplacement)
                : newName;

            return newName + extension;
        }
    }
}

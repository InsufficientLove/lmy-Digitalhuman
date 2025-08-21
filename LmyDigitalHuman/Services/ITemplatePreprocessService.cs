using System.Threading.Tasks;

namespace LmyDigitalHuman.Services
{
    /// <summary>
    /// 模板预处理服务接口
    /// </summary>
    public interface ITemplatePreprocessService
    {
        Task<bool> PreprocessTemplateAsync(string templateId, string imagePath);
        Task<bool> DeleteTemplateAsync(string templateId);
        Task<bool> VerifyTemplateAsync(string templateId);
    }
}
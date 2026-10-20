package edu.hitwh.context;

/**
 * 需要被IoC容器管理的bean的基本信息
 */
public class BeanDefination {
    private String beanName; // Bean的名字
    private Class beanClass; // Bean的Class对象
    // 实验二新增该属性。
    private String scope; // ‌基础作用域‌：singleton（单例）‌prototype（多例）

    public BeanDefination() {
    }

    public BeanDefination(String beanName, Class beanClass) {
        this.beanName = beanName;
        this.beanClass = beanClass;
    }

    // 实验二新增,替换掉之前的两个参数的全参数构造。
    public BeanDefination(String beanName, Class beanClass, String scope) {
        this.beanName = beanName;
        this.beanClass = beanClass;
        this.scope = scope;
    }

    public String getBeanName() {
        return beanName;
    }

    public void setBeanName(String beanName) {
        this.beanName = beanName;
    }

    public Class getBeanClass() {
        return beanClass;
    }

    public void setBeanClass(Class beanClass) {
        this.beanClass = beanClass;
    }

    // scope属性的getter和setter
    public String getScope() {
        return scope;
    }

    public void setScope(String scope) {
        this.scope = scope;
    }

    //@Override
    //public String toString() {
    //    return "BeanDefination{" +
    //            "beanName='" + beanName + '\'' +
    //            ", beanClass=" + beanClass +
    //            '}';
    //}

    @Override
    public String toString() {
        return "BeanDefination{" +
                "beanName='" + beanName + '\'' +
                ", beanClass=" + beanClass +
                ", scope='" + scope + '\'' +
                '}';
    }
}
